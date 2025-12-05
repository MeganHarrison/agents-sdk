# TEST PLAN: Alleato Strategic AI Project Manager

This file enumerates practical, human-verifiable acceptance criteria. Roles are tagged as [Designer], [Frontend], [Backend], [Tester]. See Validation and Acceptance in EXEC_PLAN.md for additional context.

## Environment Setup

- [Backend][Tester]
  - Precondition: Supabase project available; Storage bucket `meetings` created; SQL schema applied from EXEC_PLAN.md.
  - .env set with OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, FIREFLIES_API_KEY.
  - Backend server runs locally without errors.

- [Frontend][Tester]
  - .env.local set with NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.
  - Next.js dev server runs locally without errors.

Acceptance: Both servers reachable locally; health endpoint (if exposed) returns OK; UI renders baseline chat page.

## Ingestion: Fireflies → Supabase

- [Backend][Tester]
  1) Trigger ingestion: POST /api/ingest/fireflies with body {ids:["FF-TEST-1"]} or run dev path to ingest a local markdown file.
  2) Observe logs showing upload to storage path meetings/YYYY/MM/FF-TEST-1.md and computed content_hash.
  3) Query Supabase:
     - document_metadata has one row with fireflies_id=FF-TEST-1, non-empty summary (or placeholder), content_hash set, and full_text_url pointing to storage path.
     - documents has N>=1 rows with document_id matching metadata id, chunk_index starting at 0, token_count > 0, and embedding populated.

Acceptance: No duplicate rows on repeat ingestion; second run should report skipped or updated=0.

## Classification: Meeting → Project

- [Backend][Tester]
  1) Ensure a projects row exists (e.g., name='Project X').
  2) After ingestion, classification sets document_metadata.project_id to a valid project id and phase='Current'.
  3) A confidence score is logged or stored in metadata; low confidence triggers ML fallback as implemented.

Acceptance: Project assignment present and plausible given participants/keywords.

## Task Extraction

- [Backend][Tester]
  1) After ingestion, tasks are created or updated from the transcript.
  2) Each task has title, description, created_by='ai', and project_id set (or null if project unknown).

Acceptance: At least one reasonable task is generated for a transcript containing explicit action items.

## RAG Retrieval and Chat

- [Backend][Frontend][Tester]
  1) Ask /api/chat (or UI chat) a question scoped to a known project: "What are the biggest risks and open decisions for Project X this quarter?".
  2) The response includes an informative answer plus 3–8 citations (document_id/filename + chunk_index or direct links).
  3) Ask a recency-sensitive question: "Summarize decisions made in the last 2 weeks." and verify results cite recent transcripts.

Acceptance: Responses are grounded with citations; relevance is high; diverse sources appear (not all from a single chunk).

## UI: Projects Index and Detail

- [Frontend][Designer][Tester]
  1) Navigate to /projects; see a table with columns: Project, Phase, Meetings, Open Tasks, Last Activity.
  2) Click a project to navigate to /projects/[id]; see associated meetings with summaries, open tasks, and an AI Insights section.
  3) Use the embedded chat to ask a project-scoped question; verify project_id is sent and answers are scoped.

Acceptance: Counts match Supabase queries; navigation works; layout matches the agreed wireframes (Designer sign-off).

## Idempotence and Recovery

- [Backend][Tester]
  1) Re-run ingestion for the same Fireflies ID; verify no duplicate document_metadata nor duplicate (document_id, chunk_index) rows.
  2) Intentionally interrupt embedding mid-run (e.g., kill process); re-run; verify completion and consistent row counts.

Acceptance: Idempotent behavior and safe recovery demonstrated.

## Non-Functional

- [Tester]
  - A single transcript of ~50k tokens ingests in reasonable time (< 3 minutes on typical dev hardware with network embeddings).
  - Vector search latency for k=20 under 300ms server-side (excluding LLM rerank), measured on a small dataset.

Acceptance: Metrics recorded in test notes; any deviations documented with rationale.
