# AGENT_TASKS: Alleato Strategic AI Project Manager

This file is the source of truth for specialized roles. Keep it aligned with EXEC_PLAN.md.

## Common Notes (All Roles)

- Repository base is the OpenAI Customer Service Agents demo (Python backend + Next.js UI). Confirm actual paths with the discovery commands in EXEC_PLAN.md and record them in the plan.
- Supabase is the system of record. Use service-role key only on the backend; the UI uses the anon key. Embedding model dimension must match the DB vector column dimension.
- Idempotence is mandatory: use content_hash and upserts; avoid duplicate rows.

---

## Designer

Project: Alleato Strategic AI Project Manager

Deliverables:

- Wireframes and UI flows (PNG or Figma links documented in /docs/README.md):
  - Projects index: table with Project, Phase, Meetings, Open Tasks, Last Activity, link to detail.
  - Project detail: sections for Meetings, Open Tasks, AI Insights, and a project-scoped chat panel.
  - Chat UI adjustments for citation display and project scoping.
- Design tokens and components if needed to extend existing Chat UI.

Key Notes and Constraints:

- Prioritize information hierarchy for leadership: insights and risks must be prominent.
- Ensure citation display is readable and linkable back to meeting + chunk.
- Keep styles consistent with existing demo while supporting enterprise readability.

---

## Frontend Developer

Project: Alleato Strategic AI Project Manager

Deliverables (choose correct router; document actual paths in EXEC_PLAN.md):

- Projects index page:
  - App Router: <frontend>/app/projects/page.tsx
  - Pages Router: <frontend>/pages/projects/index.tsx
- Project detail page:
  - App Router: <frontend>/app/projects/[id]/page.tsx
  - Pages Router: <frontend>/pages/projects/[id].tsx
- Chat integration updates:
  - Update existing chat component to accept optional project_id and render citations.
- Supabase client setup: <frontend>/lib/supabaseClient.ts
- Data hooks for projects, meetings, tasks: <frontend>/lib/hooks.ts (or colocated in components).

Key Notes and Constraints:

- Use @supabase/supabase-js with NEXT_PUBLIC_* env vars.
- Projects index must show counts (meetings, open tasks) and last activity (from document_metadata.captured_at max per project).
- Project-scoped chat must send {message, project_id} to POST /api/chat and render citations with links to storage files when available.

---

## Backend Developer

Project: Alleato Strategic AI Project Manager

Deliverables:

- Supabase schema SQL file (checked into repo): /db/supabase_schema.sql (must match EXEC_PLAN.md).
- Ingestion script: /scripts/ingest_fireflies.py
- Backend modules (Python):
  - <backend>/alleato/ingest.py — Fireflies fetch, storage upload, metadata upsert, orchestration.
  - <backend>/alleato/rag.py — chunking, embeddings, retrieval, reranking.
  - <backend>/alleato/tools.py — Agents SDK tool wrappers (classify_document, extract_tasks, summarize_meeting, fetch_related_chunks, generate_insights).
- API endpoints (FastAPI/Flask):
  - GET /api/projects
  - GET /api/projects/:id
  - POST /api/chat
  - POST /api/ingest/fireflies
- Configuration and env handling: <backend>/.env.sample and README updates.

Key Notes and Constraints:

- Use OpenAI embeddings (text-embedding-3-large) unless documented otherwise; ensure documents.embedding vector dimension matches (e.g., 3072).
- Chunking: 800–1200 token windows, ~150 overlap, speaker/turn-aware; store metadata per chunk.
- Idempotent upserts: unique(fireflies_id), unique(document_id, chunk_index). Use content_hash to detect unchanged content.
- Retrieval: filter by project_id and recency when provided; LLM rerank top-50 → top-8 for answer synthesis; include citations.

---

## Tester

Project: Alleato Strategic AI Project Manager

Deliverables:

- Test checklist execution and notes in /tests/TEST_NOTES.md referencing TEST.md.
- Seed data and scripts for local testing (e.g., a sanitized sample transcript in /tests/data/).
- Metrics capture for ingestion time and retrieval latency.

Key Notes and Constraints:

- Verify acceptance criteria in TEST.md including idempotence and recovery (interrupt and re-run ingestion).
- Confirm UI counts match DB queries; validate citation links resolve to storage files.
- Record any deviations and file issues with repro steps.

===END FILE===
