"""Supabase helpers for the Alleato backend.

This module centralizes creation of the Supabase client and provides a thin
wrapper for common RAG operations (documents, chunks, and storage objects).
The implementation intentionally avoids hard-coding secrets—set the following
environment variables before importing this module:

* ``SUPABASE_URL`` – project URL, e.g. https://xyzcompany.supabase.co
* ``SUPABASE_SERVICE_ROLE_KEY`` – preferred for server-side use. Falls back to
  ``SUPABASE_ANON_KEY`` if the service key is not provided.

The official ``supabase`` Python package must be installed (add it to
``python-backend/requirements.txt``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from supabase import Client, create_client


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable '{name}' is required for Supabase access")
    return value


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase client instance."""

    url = _require_env("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or _require_env("SUPABASE_ANON_KEY")
    return create_client(url, key)


@dataclass
class DocumentChunk:
    document_id: str
    chunk_index: int
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    content_hash: Optional[str] = None


class SupabaseRagStore:
    """High-level helper for RAG-related Supabase tables."""

    def __init__(self, client: Optional[Client] = None) -> None:
        self._client = client or get_supabase_client()

    # document_metadata -------------------------------------------------
    def upsert_document_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        response = self._client.table("document_metadata").upsert(metadata).execute()
        return response.data[0] if response.data else metadata

    def fetch_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        response = (
            self._client.table("document_metadata")
            .select("*")
            .eq("id", document_id)
            .single()
            .execute()
        )
        return response.data

    def find_document_by_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        response = (
            self._client.table("document_metadata")
            .select("id", "project_id", "fireflies_id")
            .eq("content_hash", content_hash)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None

    # projects / views --------------------------------------------------
    def list_projects(self) -> List[Dict[str, Any]]:
        response = (
            self._client.table("project_activity_view")
            .select("*")
            .order("project_id")
            .execute()
        )
        return response.data or []

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        response = (
            self._client.table("project_activity_view")
            .select("*")
            .eq("project_id", project_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None

    # tasks / insights --------------------------------------------------
    def list_tasks(self, project_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        query = self._client.table("ai_tasks").select("*").limit(limit)
        if project_id is not None:
            query = query.eq("project_id", project_id)
        if status:
            query = query.eq("status", status)
        query = query.order("due_date", desc=False)
        response = query.execute()
        return response.data or []

    def upsert_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        if tasks:
            self._client.table("ai_tasks").upsert(tasks).execute()

    def list_insights(self, project_id: Optional[int] = None, limit: int = 20) -> List[Dict[str, Any]]:
        query = self._client.table("project_insights").select("*").order("captured_at", desc=True).limit(limit)
        if project_id is not None:
            query = query.eq("project_id", project_id)
        response = query.execute()
        return response.data or []

    def insert_insight(self, insight: Dict[str, Any]) -> None:
        self._client.table("project_insights").insert(insight).execute()

    # document chunks ---------------------------------------------------
    def upsert_chunks(self, chunks: List[DocumentChunk]) -> None:
        if not chunks:
            return
        rows: List[Dict[str, Any]] = []
        for chunk in chunks:
            rows.append(
                {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                    "content_hash": chunk.content_hash,
                    **({"embedding": chunk.embedding} if chunk.embedding is not None else {}),
                }
            )
        self._client.table("document_chunks").upsert(rows).execute()

    def query_chunks(self, filters: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        query = self._client.table("document_chunks").select("*").limit(limit)
        for column, value in filters.items():
            if column == "project_id":
                query = query.eq("metadata->>project_id", str(value))
            else:
                query = query.eq(column, value)
        response = query.order("created_at", desc=True).execute()
        return response.data or []

    def search_chunks_by_keyword(
        self,
        keyword: Optional[str],
        project_id: Optional[int] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        query = self._client.table("document_chunks").select("document_id", "chunk_index", "text", "metadata")
        if project_id is not None:
            query = query.eq("metadata->>project_id", str(project_id))
        if keyword:
            query = query.ilike("text", f"%{keyword}%")
        response = query.order("created_at", desc=True).limit(limit).execute()
        return response.data or []

    def fetch_recent_chunks(self, project_id: Optional[int] = None, limit: int = 5) -> List[Dict[str, Any]]:
        query = self._client.table("document_chunks").select("document_id", "chunk_index", "text", "metadata").order("created_at", desc=True).limit(limit)
        if project_id is not None:
            query = query.eq("metadata->>project_id", str(project_id))
        response = query.execute()
        return response.data or []

    def vector_search(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        try:
            response = (
                self._client.rpc(
                    "match_document_chunks",
                    {
                        "query_embedding": query_embedding,
                        "match_count": limit,
                        "match_threshold": 0.5,
                    },
                )
                .execute()
            )
            data = response.data or []
            if data:
                return data
        except Exception:
            pass
        return self.fetch_recent_chunks(limit=limit)

    # ingestion jobs ----------------------------------------------------
    def start_ingestion_job(self, fireflies_id: Optional[str], content_hash: str) -> Optional[str]:
        payload = {
            "fireflies_id": fireflies_id,
            "content_hash": content_hash,
            "status": "running",
        }
        response = self._client.table("ingestion_jobs").insert(payload).execute()
        data = response.data or []
        return data[0]["id"] if data else None

    def complete_ingestion_job(self, job_id: Optional[str], status: str, error: Optional[str] = None) -> None:
        if not job_id:
            return
        payload = {"status": status, "finished_at": datetime.utcnow().isoformat()}
        if error:
            payload["error"] = error
        self._client.table("ingestion_jobs").update(payload).eq("id", job_id).execute()


__all__ = [
    "DocumentChunk",
    "SupabaseRagStore",
    "get_supabase_client",
]
