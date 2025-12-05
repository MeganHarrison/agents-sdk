"""Utilities to ingest Fireflies markdown transcripts into Supabase."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

try:  # Optional OpenAI dependency for embeddings
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled in EmbeddingGenerator
    OpenAI = None  # type: ignore

from supabase_helpers import DocumentChunk, SupabaseRagStore

TIMESTAMP_LINE = re.compile(r"^\[(?P<stamp>\d{2}:\d{2})\]\s+\*\*(?P<speaker>.+?)\*\*:\s*(?P<text>.+)$")
SECTION_PREFIX = "## "


@dataclass
class TranscriptSegment:
    timestamp: Optional[str]
    speaker: Optional[str]
    text: str


@dataclass
class ParsedTranscript:
    title: str
    fireflies_id: Optional[str]
    captured_at: Optional[datetime]
    attendees: List[str]
    action_items: List[str]
    overview: str
    summary: str
    transcript_segments: List[TranscriptSegment]
    raw_text: str


@dataclass
class IngestionResult:
    document_id: str
    chunk_count: int
    action_item_count: int
    content_hash: str
    skipped: bool
    dry_run: bool


class EmbeddingGenerator:
    """Produces embeddings using OpenAI when available, otherwise hashed vectors."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self.model = model
        self._client = None
        if os.getenv("OPENAI_API_KEY") and OpenAI is not None:
            self._client = OpenAI()

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._client is None:
            return [self._hash_embedding(text) for text in texts]
        response = self._client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]

    @staticmethod
    def _hash_embedding(text: str, dim: int = 64) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        floats: List[float] = []
        for i in range(dim):
            byte = digest[i % len(digest)]
            floats.append((byte - 128) / 128.0)
        return floats


class FirefliesIngestionPipeline:
    """Convert Fireflies markdown exports into Supabase rows."""

    def __init__(self, store: SupabaseRagStore, embedding_model: str = "text-embedding-3-small") -> None:
        self.store = store
        self.embedder = EmbeddingGenerator(model=embedding_model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ingest_file(self, path: str | Path, project_id: Optional[int] = None, dry_run: bool = False) -> IngestionResult:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Transcript file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        parsed = self.parse_markdown(content)
        content_hash = hashlib.sha256(parsed.raw_text.encode("utf-8")).hexdigest()

        existing = self.store.find_document_by_hash(content_hash)
        document_id = (existing or {}).get("id", parsed.fireflies_id or str(uuid4()))
        skipped = existing is not None and not dry_run

        # Prepare metadata payload
        metadata = {
            "id": document_id,
            "title": parsed.title,
            "captured_at": parsed.captured_at.isoformat() if parsed.captured_at else None,
            "fireflies_id": parsed.fireflies_id,
            "summary": parsed.summary or parsed.overview,
            "content_hash": content_hash,
            "participants": ", ".join(parsed.attendees),
            "participants_array": parsed.attendees,
            "raw_text": parsed.raw_text,
            "project_id": project_id,
        }

        segments = parsed.transcript_segments
        chunks = list(self._chunk_segments(document_id, segments, project_id))

        if dry_run:
            return IngestionResult(
                document_id=document_id,
                chunk_count=len(chunks),
                action_item_count=len(parsed.action_items),
                content_hash=content_hash,
                skipped=skipped,
                dry_run=True,
            )

        job_id = self.store.start_ingestion_job(parsed.fireflies_id, content_hash)

        try:
            self.store.upsert_document_metadata(metadata)
            embeddings = self.embedder.embed([chunk.text for chunk in chunks])
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            self.store.upsert_chunks(chunks)

            tasks_payload = self._build_task_payload(parsed.action_items, document_id, project_id)
            if tasks_payload:
                self.store.upsert_tasks(tasks_payload)

            if project_id and parsed.summary:
                insight = {
                    "project_id": project_id,
                    "summary": parsed.summary[:512],
                    "detail": {"source_document_id": document_id},
                    "severity": "info",
                    "source_document_ids": [document_id],
                }
                self.store.insert_insight(insight)

            self.store.complete_ingestion_job(job_id, status="completed")
        except Exception as exc:  # pragma: no cover - network errors
            self.store.complete_ingestion_job(job_id, status="failed", error=str(exc))
            raise

        return IngestionResult(
            document_id=document_id,
            chunk_count=len(chunks),
            action_item_count=len(parsed.action_items),
            content_hash=content_hash,
            skipped=skipped,
            dry_run=False,
        )

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    def parse_markdown(self, markdown: str) -> ParsedTranscript:
        sections = self._split_sections(markdown)
        header_block = sections.get("header", "")
        title = self._extract_title(header_block) or "Untitled"
        fireflies_id = self._extract_metadata_value(header_block, "ID")
        captured_at = self._parse_datetime(self._extract_metadata_value(header_block, "Date"))
        attendees = self._parse_bullets(sections.get("Attendees", ""))
        action_items = self._parse_bullets(sections.get("Action Items", ""))
        overview = sections.get("Overview", "").strip()
        summary = sections.get("Summary Bullets", overview).strip()
        transcript_text = sections.get("Full Transcript", "")
        transcript_segments = self._parse_transcript_segments(transcript_text)

        return ParsedTranscript(
            title=title,
            fireflies_id=fireflies_id,
            captured_at=captured_at,
            attendees=attendees,
            action_items=action_items,
            overview=overview,
            summary=summary,
            transcript_segments=transcript_segments,
            raw_text=markdown,
        )

    @staticmethod
    def _split_sections(markdown: str) -> Dict[str, str]:
        sections: Dict[str, str] = {"header": ""}
        current = "header"
        buffer: List[str] = []
        for line in markdown.splitlines():
            if line.startswith(SECTION_PREFIX):
                sections[current] = "\n".join(buffer).strip()
                current = line[len(SECTION_PREFIX) :].strip()
                buffer = []
            else:
                buffer.append(line)
        sections[current] = "\n".join(buffer).strip()
        return sections

    @staticmethod
    def _extract_title(header_block: str) -> Optional[str]:
        for line in header_block.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return None

    @staticmethod
    def _extract_metadata_value(header_block: str, label: str) -> Optional[str]:
        pattern = rf"\*\*{label}:\*\*\s*(.+)"
        match = re.search(pattern, header_block)
        return match.group(1).strip() if match else None

    @staticmethod
    def _parse_datetime(raw: Optional[str]) -> Optional[datetime]:
        if not raw:
            return None
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d%H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw.strip(), fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_bullets(block: str) -> List[str]:
        items: List[str] = []
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("-"):
                items.append(stripped.lstrip("- ").strip())
        return items

    @staticmethod
    def _parse_transcript_segments(block: str) -> List[TranscriptSegment]:
        segments: List[TranscriptSegment] = []
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            match = TIMESTAMP_LINE.match(stripped)
            if match:
                segments.append(
                    TranscriptSegment(
                        timestamp=match.group("stamp"),
                        speaker=match.group("speaker"),
                        text=match.group("text"),
                    )
                )
            else:
                if segments:
                    segments[-1].text += f" {stripped}"
                else:
                    segments.append(TranscriptSegment(None, None, stripped))
        return segments

    # ------------------------------------------------------------------
    # Chunk and payload builders
    # ------------------------------------------------------------------
    def _chunk_segments(
        self,
        document_id: str,
        segments: List[TranscriptSegment],
        project_id: Optional[int],
        chunk_size: int = 12,
        overlap: int = 2,
    ) -> Iterable[DocumentChunk]:
        if not segments:
            return []
        window: List[TranscriptSegment] = []
        index = 0
        for segment in segments:
            window.append(segment)
            if len(window) >= chunk_size:
                yield self._build_chunk(document_id, index, window, project_id)
                index += 1
                window = window[-overlap:]
        if window:
            yield self._build_chunk(document_id, index, window, project_id)

    @staticmethod
    def _build_chunk(
        document_id: str,
        index: int,
        segments: List[TranscriptSegment],
        project_id: Optional[int],
    ) -> DocumentChunk:
        lines = [f"[{seg.timestamp or '??:??'}] {seg.speaker or 'Unknown'}: {seg.text}" for seg in segments]
        text = "\n".join(lines)
        metadata = {
            "chunk_index": index,
            "speakers": sorted({seg.speaker or "Unknown" for seg in segments}),
            "start_timestamp": segments[0].timestamp,
            "end_timestamp": segments[-1].timestamp,
            "project_id": project_id,
        }
        return DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            chunk_id=f"{document_id}-{index}",
            text=text,
            metadata=metadata,
            content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )

    @staticmethod
    def _build_task_payload(action_items: List[str], document_id: str, project_id: Optional[int]) -> List[Dict[str, Any]]:
        payload: List[Dict[str, Any]] = []
        for item in action_items:
            payload.append(
                {
                    "id": str(uuid4()),
                    "title": item[:120],
                    "description": item,
                    "status": "open",
                    "project_id": project_id,
                    "source_document_id": document_id,
                    "created_by": "ai",
                }
            )
        return payload
