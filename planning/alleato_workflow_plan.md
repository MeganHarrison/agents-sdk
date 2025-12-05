# Alleato Workflow Integration Plan

## Strategy Overview

- **Source of truth:** Use the Python workflow in `python-backend/alleato_agent_workflow/alleato_agent_workflow.py` as the canonical implementation. The TypeScript export stays as a reference for UI context or future client-side tooling, but it will not be wired into the runtime until we need browser-based orchestration. This keeps the backend single-language and reduces duplication.
- **Integration target:** Replace the current airline demo logic (agents/tools/guardrails defined in `python-backend/main.py`) with the Alleato workflow while preserving the FastAPI + ChatKit server scaffolding in `python-backend/api.py`.
- **Phased execution:** Stand up the Alleato workflow in isolation, then merge it into the live backend, expose new endpoints, and finally align the UI + Supabase ingestion.

## Phase 1 — Workflow Isolation
1. **Dependency audit:** Update `python-backend/requirements.txt` to include any new packages required by the Alleato workflow (e.g., `guardrails`, `openai` async client, MCP helpers). Install and verify imports locally.
2. **Secrets management:** Move hard-coded MCP credentials and API keys from the workflow file into environment variables (`.env` + `python-backend/.env.example`). Update the workflow module to read from `os.environ` with clear error messages.
3. **Module cleanup:** Split `alleato_agent_workflow.py` into logical sections:
   - configuration/constants
   - guardrail utilities
   - tool definitions (MCP, web search)
   - agent definitions (classification agent, project agent, etc.)
   Add docstrings so future contributors can navigate it easily.
4. **Smoke test script:** Create a simple CLI entry point (e.g., `python-backend/scripts/run_alleato_workflow.py`) that imports the workflow module, feeds a sample conversation, and prints results. This proves the workflow runs without the rest of the stack.

## Phase 2 — Backend Integration
1. **Context alignment:** Extend `AirlineAgentContext` (or create a new `AlleatoAgentContext`) to track project IDs, transcript references, Supabase links, etc. Decide whether to keep both contexts side-by-side with a feature flag or fully replace the airline one.
2. **Server wiring:** In `api.py`, add a configuration switch (env var or query parameter) to select between the old airline agents and the new Alleato workflow while we migrate. Eventually remove the airline path once the new workflow is stable.
3. **Guardrail pipeline:** Replace the current guardrail handling in `api.py` with calls into the workflow’s guardrail helpers so ChatKit still receives tripwire events and masked text. Ensure the guardrail outputs map to `GuardrailCheck` for UI display.
4. **State persistence:** Update `ConversationState` to capture any workflow-specific metadata (e.g., selected project, recent insights). Make sure snapshot endpoints expose the new fields for the UI.

## Phase 3 — Supabase + RAG Plumbing
1. **Supabase client layer:** Build a Python service module that wraps Supabase Storage + Postgres access (projects, document metadata, embeddings). This will back the MCP tools and any direct queries from the workflow.
2. **Ingestion hooks:** Connect the existing Fireflies ingestion scripts with Supabase so new transcripts automatically populate the datastore expected by the workflow.
3. **Retriever tooling:** Implement reusable retrieval helpers that the Alleato agent can call (vector search + metadata filters). Register them as MCP tools or direct function tools depending on the workflow’s expectations.

## Phase 4 — API & UI Updates
1. **REST endpoints:** Add `/api/projects`, `/api/projects/:id`, and `/api/chat` routes aligned with the workflow’s outputs (tasks, insights, citations). Document request/response shapes.
2. **UI components:** Update `ui/components/agent-panel-rag.tsx`, `agents-list.tsx`, and related views to consume the new endpoints and display Alleato-specific data (projects, tasks, insights, guardrails).
3. **Feature toggle removal:** Once the new UI + backend paths are stable, remove the airline demo code and dead routes.

## Phase 5 — Validation & Docs
1. **End-to-end tests:** Script regression checks (ingest transcript → Supabase → chat question → citations) plus guardrail cases. Manual checklists are fine initially; aim for automated pytest coverage later.
2. **Operational docs:** Update `README.md`, `multiagent_workflow/EXEC_PLAN.md`, and create an onboarding guide detailing env setup, Supabase config, MCP credentials, and deployment steps.
3. **Handoff readiness:** Ensure `.agent` planning docs capture the final architecture, data flows, and maintenance notes so others can continue the project.

## Open Questions / Follow-ups
- Do we need the TypeScript workflow for any future “local agent builder” UI? If so, park a TODO to revisit after backend integration.
- What Supabase schema changes (if any) are still pending compared to the workflow’s expectations? Align this plan with the schema defined in `EXEC_PLAN.md`.
- Confirm the guardrail bundle configuration (PII, moderation, jailbreak) matches the organization’s compliance requirements before going live.
