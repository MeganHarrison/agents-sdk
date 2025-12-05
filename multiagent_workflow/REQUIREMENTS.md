# REQUIREMENTS: Alleato Strategic AI Project Manager

## Product Goals

- Transform the OpenAI Customer Service Agents demo into a strategic, organization-wide AI project manager for Alleato.
- Centralize institutional memory by ingesting three+ years of Fireflies meeting transcripts.
- Provide a conversational AI that detects patterns, risks, opportunities, commitments, and tasks; offers strategic guidance; and ensures accountability.
- Organize knowledge by Projects and Phases; present project dashboards and insights.

## Target Users

- Leadership: needs cross-project visibility, risks/opportunities, and accountability tracking.
- Project contributors: need project context, decisions, tasks, and a chat interface to query history and plan work.
- Operations/PM: need reliable ingestion, classification, and task generation at scale.

## Key Features

- Ingestion from Fireflies to Supabase Storage (bucket: meetings).
- Metadata table (document_metadata) capturing Fireflies ID, participants, summary, full content link, captured_at, content_hash, project_id, phase.
- Vectorized chunks table (documents) using pgvector with embeddings for RAG.
- Projects table and per-project dashboards; Tasks table for AI-generated assignments.
- Chat agent (Agents SDK) that uses RAG, cites sources, classifies meetings to projects, extracts decisions/tasks/risks, and generates insights.
- Projects index page and Project detail pages in Next.js UI.

## Constraints and Assumptions

- Supabase is the source of truth for storage, metadata, embeddings, projects, and tasks.
- Embeddings via OpenAI (e.g., text-embedding-3-large); documents.embedding vector dimension must match the chosen model.
- Idempotent ingestion required: content_hash-based upserts; unique constraints on fireflies_id and (document_id, chunk_index).
- Meeting → Project classification must work without explicit labels using participants, filename, and content semantics.
- Privacy/security: use service role key on backend only; RLS for production.

## Observable Behaviors (High Level)

- Importing a transcript creates a storage object and a document_metadata row with summary and content_hash.
- Chunking and embedding populate documents with ~800–1200 token chunks per transcript.
- Project classification assigns project_id and phase='Current' with a confidence score.
- Task extraction creates actionable tasks with titles, descriptions, and optional assignees/due_dates.
- Chat responses include 3–8 citations to transcript chunks and can be scoped to a project.
- Projects index lists each project with counts (meetings, open tasks) and last activity; detail pages show meetings, tasks, and insights.

## Out of Scope (Initial)

- Full-blown decisions/insights separate tables (optional; can use metadata JSON initially).
- Advanced access controls beyond basic RLS; SSO.
- Automated notifications to employees (follow-up integrations can be added later).
