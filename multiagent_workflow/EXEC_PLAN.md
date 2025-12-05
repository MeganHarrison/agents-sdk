# Alleato Strategic AI Project Manager (RAG + Supabase + Agents SDK)

This ExecPlan is a living document. Maintain it in accordance with ../.agent/PLANS.md. Update Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective as work proceeds. This file must remain fully self-contained so a novice can implement the change end-to-end.

## Purpose / Big Picture

We will transform the OpenAI Customer Service Agents demo into Alleato's AI Chief of Staff — an executive-level strategic intelligence system that functions as the company's institutional memory and thinking partner. This system ingests years of Fireflies meeting transcripts, builds multi-resolution knowledge representations, and provides strategic synthesis beyond simple retrieval.

**The system will act as a strategic partner that:**
- Maintains perfect recall of every meeting, decision, and commitment across 3+ years
- Detects patterns, systemic issues, and emerging opportunities across all projects
- Provides root cause analysis and strategic recommendations, not just search results
- Tracks accountability and follow-through automatically
- Synthesizes insights across time, projects, and people
- Becomes smarter with each meeting, building institutional knowledge

**Users will experience:**
- An AI that answers strategic questions like "What systemic issues are blocking our ASRS deployments?" with pattern analysis across dozens of meetings
- Automatic extraction and tracking of decisions, risks, and opportunities
- Project intelligence dashboards showing meeting progressions, risk evolution, and decision impact
- Conversational interface that provides strategic guidance, not just citations
- Proactive alerts on unresolved risks, broken commitments, and emerging patterns

**Technical Architecture:**
- Multi-resolution knowledge: meeting summaries → segment summaries → chunks → structured entities
- Two-stage retrieval: meeting selection → focused chunk retrieval
- Hybrid search: dense vectors (70%) + BM25 keyword (30%) with MMR diversity
- Strategic synthesis layer: pattern detection → root cause analysis → recommendations

## Progress

Track actual progress here with timestamps (UTC) as work happens. Every checkbox represents a specific deliverable.

- [x] (2025-12-05 00:00Z) Wrote initial ExecPlan in accordance with ../.agent/PLANS.md.
- [x] (2025-12-05 04:30Z) Enhanced RAG strategy with hybrid search, semantic chunking, MMR reranking, and RAGAS metrics.
- [x] (2025-12-05 05:00Z) Incorporated strategic intelligence architecture from plan-ai-pm.md.
- [x] (2025-12-05 06:00Z) Reorganized to MVP-first approach for iterative development.
- [x] (2025-12-05 11:10Z) Regenerated Supabase client types and documented the schema additions (document_chunks, ai_tasks, project_insights, ingestion_jobs, views).
- [x] (2025-12-05 11:45Z) Implemented Supabase helper module, Fireflies ingestion pipeline, REST endpoints (/api/projects, /api/projects/:id, /api/chat, /api/ingest/fireflies), and FastAPI-based RAG chat scaffolding with unit tests.
- [x] (2025-12-05 12:20Z) Added Projects index/detail Next.js routes, project/lib utilities, and wired frontend calls to the new backend endpoints.

## Implementation Approach — MVP First, Then Advanced Features

**Rationale for Phased Approach:**
Instead of implementing all advanced features at once, we're taking an iterative approach:

### Phase Summary:
- **Phase 0**: Environment Setup ✅ (mostly complete)
- **Phase 1**: MVP RAG - Basic chat with simple vector search 🎯 **START HERE**
- **Phase 2**: Enhanced Schema - Add all strategic intelligence tables
- **Phase 3**: Advanced Ingestion - Segmentation and entity extraction
- **Phase 4**: Advanced Retrieval - Two-stage and hybrid search
- **Phase 5**: Strategic Synthesis - Pattern analysis and recommendations
- **Phase 6**: Agent Tools & APIs - Complete tool suite
- **Phase 7**: Testing & Evaluation - Quality metrics and benchmarks
- **Phase 8**: UI Development - Project dashboards
- **Phase 9**: Production Ready - Security and deployment

**Why MVP First?**
1. **Verify Core Functionality**: Ensure Supabase connection and embedding retrieval work
2. **Debug Early**: Identify integration issues with minimal complexity
3. **Quick Win**: Get a working chat in hours, not weeks
4. **Iterative Enhancement**: Add features incrementally with working baseline
5. **Risk Reduction**: Validate architecture before investing in advanced features

### Phase 0 — Environment Setup
- [x] Clone OpenAI CS Agents demo repository
- [x] Set up Python virtual environment with required packages
- [x] Configure Next.js frontend development environment
- [x] Create Supabase project and obtain API keys
- [x] Set up .env files with all required API keys
- [x] Verify baseline demo runs locally (backend + frontend)
- [ ] Create development branch for Alleato modifications

### Phase 1 — MVP RAG Implementation (Basic Connectivity & Retrieval)
**Goal: Get a minimal working chat with basic vector search to verify Supabase connectivity and embedding retrieval.**

- [x] (2025-12-05 09:00Z) Review and document how agents and chat are currently setup
- [x] (2025-12-05 09:15Z) Create a copy of the current chat page to utilize for new MVP RAG chat
- [x] (2025-12-05 09:30Z) Update EXEC_PLAN with every step needed to transition the new page to the RAG version
- [x] (2025-12-05 09:45Z) Configured automatic .env loading for all Python files
- [x] (2025-12-05 09:50Z) Updated Supabase MCP token and installed Supabase Python SDK
- [x] (2025-12-05 09:55Z) Verified Supabase connection working via Python SDK

#### Current Architecture Documentation
**Backend Structure (Python/FastAPI):**
- `python-backend/api.py`: FastAPI server with ChatKit integration, routes to `/chatkit`
- `python-backend/main.py`: 5 airline agents with handoff mechanism
- `python-backend/memory_store.py`: In-memory conversation storage
- Current agents: triage_agent, seat_booking_agent, flight_status_agent, cancellation_agent, faq_agent

**Frontend Structure (Next.js):**
- `ui/app/page.tsx`: Main page with AgentPanel and ChatKitPanel components
- `ui/components/chatkit-panel.tsx`: ChatKit UI wrapper with airline prompts
- Uses @openai/chatkit-react for chat interface
- Connects to backend via `/chatkit` proxy

#### Transition Steps for RAG Version

##### Frontend Changes:
- [x] Create new route `/rag-chat` by copying current page
  - [x] Copy `ui/app/page.tsx` to `ui/app/rag-chat/page.tsx`
  - [x] Create new `ui/components/rag-chatkit-panel.tsx` component
- [x] Update starter prompts in RAG chat panel to Alleato-focused quick starts (recent decisions, risks, tasks, pattern analysis) inside `ui/components/rag-chatkit-panel.tsx`.
- [ ] Modify AgentPanel to show RAG-specific information:
  - [ ] Add "Sources Retrieved" section
  - [ ] Add "Confidence Score" display
  - [ ] Show "Query Type" classification
- [ ] Update context display for RAG:
  - [ ] Show current project filter
  - [ ] Display number of documents searched
  - [ ] Show retrieval latency

##### Backend Changes:
- [x] Introduce `SupabaseRagStore` and ingestion pipeline (see `python-backend/supabase_helpers.py` and `python-backend/ingestion/fireflies_pipeline.py`) to replace the placeholder agent stubs for the MVP.
- [x] Expose REST endpoints (`/api/projects`, `/api/projects/{id}`, `/api/chat`, `/api/ingest/fireflies`) plus `/rag-chatkit` inside `python-backend/api.py`, with FastAPI dependency overrides for testing.
- [ ] Create new RAG-specific Agent SDK tools (vector search, formatted context, etc.) for ChatKit orchestration once Phase 4 retrieval lands.
- [ ] Implement richer RAG session context (query classification, retrieved chunk history, structured evidence) to replace the current minimal dictionary returned by `/api/chat`.
  ```python
  class RAGContext(BaseModel):
      query: str | None = None
      retrieved_chunks: list[dict] = []
      sources: list[str] = []
      confidence_score: float = 0.0
      query_type: str | None = None  # fact/status/pattern/risk/strategy
  ```

##### Configuration Updates:
- [x] Add Supabase environment variables (see `python-backend/.env.example` for canonical keys loaded via `dotenv`).
- [x] Update Next.js config (`ui/next.config.mjs`) for `/rag-chatkit` and REST proxies.
- [x] Add proxy for `/rag-chatkit` endpoint (see rewrites list above).

#### Phase 1A — Basic Database Setup
- [x] Create Supabase storage bucket 'meetings' for transcripts.
- [x] Enable pgvector extension.
- [x] Set up Supabase Client with Supabase UI Library.
- [x] Generate Supabase types (see `types/database_types.ts`) so frontend and backend share the same schema contracts.
- [x] Review existing database schema and align with the fact that `document_metadata.id` is `text`; document this constraint for future migrations.
- [x] Replace the placeholder documents table with the implemented `public.document_chunks`, `public.ai_tasks`, `public.project_insights`, and `public.ingestion_jobs` tables plus related indexes/triggers. These match the plan’s richer schema while remaining compatible with current data.

#### Phase 1B — Basic Ingestion Pipeline
- [x] Create reusable ingestion pipeline (`python-backend/ingestion/fireflies_pipeline.py`) capable of parsing markdown exports, computing hashes, chunking content, generating embeddings, and upserting metadata/chunks/tasks/insights.
- [x] Support dry-run mode for safe testing using the included fixture (`python-backend/tests/fixtures/sample_transcript.md`).
- [x] Add unit coverage via `python-backend/tests/test_fireflies_pipeline.py` to ensure parsing, dry-run behavior, and Supabase call contract compliance.

#### Phase 1C — Basic Vector Retrieval
- [x] Implement Supabase-backed helper (`SupabaseRagStore` in `python-backend/supabase_helpers.py`) that encapsulates metadata upserts, chunk writes, keyword search, vector search (with RPC fallback), and structured fetches.
- [x] Provide a simple keyword fallback plus recent-chunk retrieval to keep chat responsive even before HyDE/MMR land.
- [x] Add smoke tests (`python-backend/test_rag_retrieval.py`) to exercise the helper against live data.

#### Phase 1D — Basic Chat Integration
- [x] Expose REST endpoints in `python-backend/api.py`:
    - `/api/projects` and `/api/projects/{id}` aggregate Supabase views and related tasks/insights.
    - `/api/chat` performs keyword-aided retrieval and returns reply + sources + structured artifacts.
    - `/api/ingest/fireflies` invokes the ingestion pipeline, supporting dry runs for local fixtures.
- [x] Cover endpoints through `python-backend/tests/test_api_endpoints.py` using FastAPI's `TestClient` and dependency overrides.

#### Phase 1E — MVP Validation
- [x] Verify Supabase connectivity via helper scripts/tests; regenerate types after schema changes.
- [x] Confirm embeddings and chunks persist and can be retrieved via `/api/chat` and helper scripts.
- [x] Document limitations (e.g., current retrieval is keyword + RPC, AgentPanel UI still airline-themed) for follow-up.

### Phase 2 — Enhanced Database Schema (Strategic Intelligence Foundation)
**Goal: Once MVP is working, add the full schema for multi-resolution knowledge and structured entities.**

- [ ] Create core organizational tables (baseline in place, semantics pending):
  - [x] projects table with phase tracking (existing construction-era table reused; now surfaced via `project_activity_view`).
  - [x] document_metadata table for meeting records (already populated; documentation updated to reflect text primary keys).
  - [ ] meeting_segments table for semantic segmentation (still pending; current MVP operates at chunk granularity).
- [ ] Enhance documents table with additional fields:
  - [ ] Add segment_id foreign key
  - [ ] Add chunk_type, semantic_density, speaker_transitions
  - [ ] Add topic_keywords array for BM25 search
  - [ ] Add speakers array
- [ ] Create structured knowledge tables:
  - [ ] decisions table with embeddings
  - [ ] risks table with categorization
  - [ ] opportunities table with type classification
  - [x] tasks table with accountability tracking (implemented as `public.ai_tasks`).
  - [ ] commitments table for follow-through
- [ ] Create performance optimization tables:
  - [ ] query_cache table for caching
  - [ ] rag_metrics table for evaluation
- [ ] Add all required indexes:
  - [ ] Additional vector indexes for new embedding columns
  - [ ] GIN indexes for full-text search
  - [ ] B-tree indexes for all foreign keys
  - [ ] Composite indexes for common query patterns
- [ ] Set up RLS policies for production security

### Phase 3 — Advanced Ingestion Pipeline (Segmentation & Extraction)
**Goal: Upgrade from basic chunking to sophisticated segmentation and structured knowledge extraction.**

#### Fireflies API Integration:
- [ ] Implement authentication and rate limiting
- [ ] Build transcript fetching with pagination
- [ ] Add error recovery and retry logic
- [ ] Create batch processing for historical data

#### Meeting Preprocessing:
- [ ] Strip boilerplate and normalize text
- [ ] Extract and standardize speaker labels
- [ ] Parse timestamps and convert to seconds
- [ ] Compute content hash for deduplication

#### LLM-Based Semantic Segmentation (NEW):
- [ ] Use GPT-4 to identify 5-10 topic segments per meeting
- [ ] Generate segment titles and summaries
- [ ] Extract decisions/risks/tasks per segment
- [ ] Store segments in meeting_segments table

#### Semantic Chunking Within Segments:
- [ ] Implement topic boundary detection (similarity < 0.7)
- [ ] Create 800-1200 token chunks within segment boundaries
- [ ] Calculate semantic density scores
- [ ] Preserve speaker transitions in chunks
- [ ] Extract keywords for BM25 search

#### Multi-Resolution Embeddings:
- [ ] Generate meeting-level summary embeddings
- [ ] Create segment-level embeddings
- [ ] Maintain chunk-level embeddings (enhanced from MVP)
- [ ] Add entity-level embeddings for structured knowledge

#### Structured Entity Extraction:
- [ ] Extract decisions with rationale and impact
- [ ] Identify risks with likelihood and mitigation
- [ ] Detect opportunities with value assessment
- [ ] Extract tasks with assignee and due dates
- [ ] Track commitments for accountability

#### Idempotent Storage Pipeline:
- [ ] Implement upserts for all tables
- [ ] Handle partial failures gracefully
- [ ] Add transaction support for consistency
- [ ] Create audit logging for ingestion

### Phase 4 — Advanced Retrieval System (Two-Stage & Hybrid)
**Goal: Upgrade from basic vector search to sophisticated two-stage retrieval with hybrid search.**

#### Query Classification:
- [ ] Build query type classifier (fact/status/pattern/risk/strategy)
- [ ] Route queries to optimal retrieval strategy
- [ ] Implement query intent detection
- [ ] Add confidence scoring for classification

#### Two-Stage Retrieval Pipeline:
- [ ] Stage 1: Meeting selection via summaries
- [ ] Stage 2: Chunk retrieval within selected meetings
- [ ] Implement meeting relevance scoring
- [ ] Add result merging and deduplication

#### Hybrid Search Implementation:
- [ ] Add BM25/full-text search alongside vectors
- [ ] Implement Reciprocal Rank Fusion (RRF)
- [ ] Add temporal decay scoring
- [ ] Include participant/project boosting

#### Query Enhancement:
- [ ] Extract entities from queries
- [ ] Implement synonym expansion
- [ ] Add HyDE for complex questions
- [ ] Generate query variations

#### Multi-Stage Reranking:
- [ ] Implement cross-encoder reranking
- [ ] Add MMR for diversity (λ=0.5)
- [ ] Calculate confidence scores
- [ ] Expand context windows

#### Pattern Detection:
- [ ] Identify recurring themes
- [ ] Analyze cross-project patterns
- [ ] Detect temporal trends
- [ ] Flag anomalies

#### Performance Optimization:
- [ ] Implement query result caching
- [ ] Add embedding cache for hot chunks
- [ ] Set up cache invalidation
- [ ] Monitor cache performance

### Phase 5 — Strategic Synthesis Layer
**Goal: Transform raw retrieval into strategic intelligence with pattern analysis and recommendations.**

#### Synthesis Pipeline:
- [ ] Implement result clustering by theme
- [ ] Build pattern aggregation across meetings
- [ ] Add root cause analysis capabilities
- [ ] Create impact assessment framework

#### Strategic Reasoning:
- [ ] Detect systemic issues across projects
- [ ] Identify emerging opportunities
- [ ] Analyze risk correlations
- [ ] Track decision impact over time

#### Recommendation Engine:
- [ ] Generate process improvement suggestions
- [ ] Create risk mitigation strategies
- [ ] Propose resource optimizations
- [ ] Develop strategic next steps

#### Response Enhancement:
- [ ] Format responses with analysis layers
- [ ] Add confidence scoring
- [ ] Generate follow-up questions
- [ ] Include evidence citations

### Phase 6 — Agent Tools & API Endpoints
**Goal: Build the complete set of agent tools and HTTP endpoints for the full system.**

#### Core Agent Tools:
- [ ] fetch_related_chunks (integrate two-stage retrieval)
- [ ] fetch_temporal_context (chronological progression)
- [ ] fetch_cross_project_patterns (pattern detection)
- [ ] classify_document_to_project (auto-classification)
- [ ] extract_structured_entities (decisions/risks/tasks)
- [ ] generate_strategic_insights (synthesis)
- [ ] evaluate_retrieval_quality (RAGAS metrics)
- [ ] track_commitment_status (accountability)

#### HTTP API Endpoints:
- [ ] GET /api/projects (with aggregated metrics)
- [ ] GET /api/projects/:id (detailed project view)
- [ ] POST /api/chat (enhanced from MVP)
- [ ] POST /api/ingest/fireflies (batch ingestion)
- [ ] GET /api/decisions (filtered/paginated)
- [ ] GET /api/risks (with status tracking)
- [ ] GET /api/opportunities (by type/status)
- [ ] GET /api/metrics/rag (quality metrics)
- [ ] GET /api/insights/patterns (detected patterns)

#### Conversation Management:
- [ ] Implement session state tracking
- [ ] Add context accumulation
- [ ] Generate smart follow-ups
- [ ] Enable action item creation from chat

### Phase 7 — Evaluation & Testing
**Goal: Comprehensive testing of all system components with quality metrics.**

#### Test Dataset Creation:
- [ ] Prepare 3-5 sample transcripts with ground truth
- [ ] Create 50 test queries with expected answers
- [ ] Document known decisions/risks/tasks for validation
- [ ] Build regression test suite

#### RAGAS Evaluation Implementation:
- [ ] Set up faithfulness scoring
- [ ] Implement answer relevance measurement
- [ ] Add context precision calculation
- [ ] Create context recall assessment

#### Performance Benchmarking:
- [ ] Test query latency (target P95 < 1.5s)
- [ ] Monitor cache hit rates
- [ ] Measure ingestion throughput
- [ ] Profile memory usage

#### Quality Validation:
- [ ] Test proper noun recall (target >90%)
- [ ] Validate topic boundary accuracy (>80%)
- [ ] Verify semantic density scores (>0.7)
- [ ] Check pattern detection accuracy

### Phase 8 — UI Development (Project Intelligence Dashboard)
**Goal: Build comprehensive UI for project intelligence and enhanced chat interface.**

#### Projects Index Page:
- [ ] Create project table with metrics
- [ ] Add meeting count aggregation
- [ ] Display open task counts
- [ ] Show risk status indicators
- [ ] Track last activity
- [ ] Implement search and filtering

#### Project Detail Page:
- [ ] Build meeting timeline view
- [ ] Show decision history
- [ ] Track risk evolution
- [ ] Display task burndown
- [ ] Create opportunity pipeline
- [ ] Add project-scoped chat

#### Insights Dashboard:
- [ ] Visualize detected patterns
- [ ] Create risk heatmap
- [ ] Track decision impact
- [ ] Show commitment status

#### Enhanced Chat Interface:
- [ ] Display citations with confidence scores
- [ ] Link to source documents
- [ ] Show follow-up suggestions
- [ ] Enable action item creation
- [ ] Add query type indicators

### Phase 9 — Integration & Production Readiness
**Goal: Final integration, security hardening, and deployment preparation.**

#### Frontend-Backend Integration:
- [ ] Configure Supabase client
- [ ] Set up real-time subscriptions
- [ ] Implement optimistic updates
- [ ] Add comprehensive error handling

#### Data Management:
- [ ] Set up SWR/React Query
- [ ] Implement cache strategies
- [ ] Add pagination throughout
- [ ] Create loading/error states

#### Security & Operations:
- [ ] Implement API rate limiting
- [ ] Add authentication/authorization
- [ ] Sanitize all inputs
- [ ] Set up audit logging
- [ ] Create health check endpoints
- [ ] Implement graceful degradation
- [ ] Add circuit breakers
- [ ] Configure retry strategies

#### Monitoring & Documentation:
- [ ] Set up application metrics
- [ ] Track business KPIs
- [ ] Configure alerting
- [ ] Create monitoring dashboards
- [ ] Write API documentation
- [ ] Create user guide
- [ ] Document admin procedures
- [ ] Build troubleshooting guide

#### Deployment:
- [ ] Configure environments (dev/staging/prod)
- [ ] Set up CI/CD pipeline
- [ ] Create database migration scripts
- [ ] Document rollback procedures
- [ ] Prepare deployment checklist

## Surprises & Discoveries

Record unexpected behaviors and supporting evidence here during implementation.

- Observation: `document_metadata.id` is stored as `text` throughout the legacy schema, so new tables must use `text` foreign keys. The initial attempt to declare UUID FKs failed (Postgres 42804) until the plan was updated.
  Evidence: `ERROR: 42804: foreign key constraint "document_chunks_document_id_fkey" cannot be implemented` during schema migration.

- Observation: Historical Fireflies IDs contain duplicates, preventing immediate creation of the `ux_document_metadata_fireflies` unique index. The plan now notes that ingestion must deduplicate before enabling the constraint.
  Evidence: `ERROR: 23505 ... Key (fireflies_id)=(01K4D6PY78A37RHQK7WA4282CA) is duplicated.`

## Decision Log

Record all design decisions with rationale.

- Decision: Use Supabase (Postgres + pgvector) as the vector store and source of truth for transcripts, metadata, embeddings, projects, and tasks.
  Rationale: Single managed backend with storage, row-level security (RLS), and vector search in one place; good SDKs for Python and Next.js.
  Date/Author: 2025-12-05 / PM

- Decision: Implement "semantic + turn-level chunking" with 800–1200 token targets and ~150 token overlap; store both chunk text and key metadata with content hash for idempotent upserts.
  Rationale: Transcripts are long, conversational, and topic-shifting; turn-aware chunks improve retrieval precision while overlap preserves context.
  Date/Author: 2025-12-05 / PM

- Decision: Meeting → Project classification via hybrid heuristics (participants, filename, keyword/topic embeddings) plus model-assisted classification where confidence is low.
  Rationale: Many transcripts lack explicit project labels; a deterministic first pass with ML fallback yields reliability and coverage.
  Date/Author: 2025-12-05 / PM

- Decision: Use OpenAI embeddings for RAG (e.g., text-embedding-3-large) and reranking via lightweight LLM scoring for top-k to boost relevance.
  Rationale: High-quality embeddings and simple reranking often outperform complex pipelines on conversational corpora.
  Date/Author: 2025-12-05 / PM

- Decision: Implement hybrid search combining dense vector (70%) + BM25 keyword search (30%) for improved recall on names, acronyms, and specific terms.
  Rationale: Meeting transcripts contain many proper nouns and company-specific terminology that benefit from keyword matching.
  Date/Author: 2025-12-05 / PM (Updated)

- Decision: Use semantic chunking with topic boundaries detection plus fallback to fixed-size chunks for coherent retrieval units.
  Rationale: Topic shifts in meetings create natural boundaries; semantic chunking preserves context better than arbitrary splits.
  Date/Author: 2025-12-05 / PM (Updated)

- Decision: Implement MMR (Maximal Marginal Relevance) reranking with λ=0.5 for diversity in multi-meeting contexts.
  Rationale: Prevents redundant information from dominating results when similar points are discussed across multiple meetings.
  Date/Author: 2025-12-05 / PM (Updated)

- Decision: Add query expansion with HyDE (Hypothetical Document Embeddings) for complex strategic questions.
  Rationale: Business strategy queries benefit from generating hypothetical answers to improve semantic matching.
  Date/Author: 2025-12-05 / PM (Updated)

- Decision: Implement two-tier caching: embedding cache (Redis) and query result cache with 15-minute TTL.
  Rationale: 3+ years of transcripts require optimization; caching reduces latency for repeated queries.
  Date/Author: 2025-12-05 / PM (Updated)

- Decision: Add meeting segmentation layer between meetings and chunks for better semantic organization.
  Rationale: Meetings have natural topic boundaries (agenda items); segmenting first dramatically improves retrieval relevance and enables segment-level summaries.
  Date/Author: 2025-12-05 / PM (Strategic Update)

- Decision: Build structured knowledge tables (decisions, risks, opportunities) separate from raw text.
  Rationale: Strategic intelligence requires structured data for pattern analysis, not just text retrieval. This enables "thinking" vs just "remembering".
  Date/Author: 2025-12-05 / PM (Strategic Update)

- Decision: Implement two-stage retrieval: first find relevant meetings, then retrieve chunks within those meetings.
  Rationale: Prevents irrelevant chunks from other meetings diluting results; improves precision while maintaining recall.
  Date/Author: 2025-12-05 / PM (Strategic Update)

- Decision: Add query classification to route different query types to appropriate retrieval strategies.
  Rationale: Fact lookups need different retrieval than strategic planning questions; routing improves both speed and relevance.
  Date/Author: 2025-12-05 / PM (Strategic Update)

- Decision: Implement strategic synthesis layer that performs pattern detection and root cause analysis before answering.
  Rationale: The system should act as a strategist providing insights, not a search engine returning snippets.
  Date/Author: 2025-12-05 / PM (Strategic Update)

- Decision: Preserve the existing `text` primary keys in `document_metadata` and use `text` foreign keys in new tables (`document_chunks`, `ai_tasks`, `project_insights`, `ingestion_jobs`).
  Rationale: The construction-era Supabase schema stores meeting IDs as `text`; attempting to coerce to UUID breaks existing data and prevented foreign key creation. Aligning with the current type keeps migrations incremental.
  Date/Author: 2025-12-05 / Codex

- Decision: Provide a hashed-embedding fallback inside the ingestion pipeline when `OPENAI_API_KEY` is absent or rate-limited.
  Rationale: Local tests and CI need deterministic embeddings without external calls; hashing keeps chunk ordering compatible while still exercising vector search code paths.
  Date/Author: 2025-12-05 / Codex

## Outcomes & Retrospective

Populate at major milestones and at completion.

- Milestone 1 (Dev up): Baseline OpenAI CS Agents demo confirmed working end-to-end (backend + frontend), providing a stable starting point.
- Milestone 2 (Supabase schema + ingestion): Implemented chunk/tables (`document_chunks`, `ai_tasks`, `project_insights`, `ingestion_jobs`), regenerated Supabase types, and shipped the Fireflies ingestion pipeline plus unit tests.
- Milestone 3 (RAG + classification): MVP `/api/chat` endpoint now performs Supabase retrieval (vector + keyword fallback) and returns structured artifacts; `/api/projects` surfaces aggregated metrics for the frontend.
- Milestone 4 (UI: Projects + detail + chat): Initial `/projects` and `/projects/[id]` routes display live data via the new APIs; RAG chat UI exists at `/rag-chat` though AgentPanel enhancements remain outstanding.
- Final: …

## Context and Orientation

Repository baseline: a clone of https://github.com/openai/openai-cs-agents-demo.git which provides:

- A Python backend that orchestrates Agents SDK logic.
- A Next.js UI that visualizes orchestration and provides a chat interface using ChatKit UI.

Because forks vary slightly, first identify the actual backend and frontend folders in this repo. Run these commands from the repository root to discover paths and set shell variables for the rest of this plan:

```
# Discover likely frontend and backend directories by common names
FRONTEND_DIR=$(ls -d */ | egrep -i 'web|ui|frontend|next|app' | head -n1)
BACKEND_DIR=$(ls -d */ | egrep -i 'server|api|backend|python|app' | head -n1)
echo "FRONTEND_DIR=$FRONTEND_DIR"
echo "BACKEND_DIR=$BACKEND_DIR"
```

If the discovery fails, inspect the tree manually and set FRONTEND_DIR and BACKEND_DIR accordingly. The demo typically has a Next.js app (e.g., web/) and a Python backend (e.g., server/ or backend/).

Primary external systems and keys:

- Supabase project: SUPABASE_URL, SUPABASE_ANON_KEY (frontend), SUPABASE_SERVICE_ROLE_KEY (backend/scripts).
- Fireflies API key: FIREFLIES_API_KEY for transcript export.
- OpenAI API key: OPENAI_API_KEY for embeddings and LLM.

Key repo paths introduced during Phase 1:

- `python-backend/supabase_helpers.py` centralizes Supabase access (metadata/chunks/tasks/insights) and is imported by API routes and the ingestion pipeline.
- `python-backend/ingestion/fireflies_pipeline.py` implements `FirefliesIngestionPipeline`, which powers `/api/ingest/fireflies` and the unit tests.
- `python-backend/tests/` contains new fixtures and FastAPI/ingestion tests that can be run via `PYTHONPATH=python-backend python -m unittest ...`.
- `ui/app/projects/` and `ui/app/projects/[id]/` render the new project dashboards backed by `/api/projects` endpoints.

## Plan of Work (Phased)

Narrative overview of the sequence of edits grouped by delivery phases.

### Phase 1 — Strategic Intelligence Foundation
Goal: Build the complete ingestion, segmentation, knowledge extraction, and two-stage retrieval system that powers strategic intelligence.

1) Local dev bring-up
   - Install Python (>=3.10) and Node.js (>=18). Install project deps for backend and frontend. Start both servers to establish a working baseline.

2) Supabase data model and storage
   - Create a storage bucket meetings for transcript markdown files.
   - Create Postgres tables:
     - document_metadata: one row per transcript with Fireflies ID, filename, participants, captured_at, summary, full_text_url, content_hash, project_id (nullable), phase (default 'Current'), and raw_text (optional for convenience if size permits).
     - documents: pgvector-backed chunk store with document_id (FK to document_metadata), chunk_id, chunk_text, chunk_index, token_count, embedding vector, content_hash, and JSONB metadata.
     - projects: stable list of projects with id, name, description, phase, owners, participants, created_at, updated_at.
     - tasks: AI-created tasks with id, project_id, source_document_id, title, description, assignee, status, due_date, created_by ('ai'|'human'), created_at, updated_at.
   - Add necessary indexes and constraints; enable the vector extension.

3) Ingestion and enrichment pipeline
   - Fireflies fetcher: periodically or on-demand fetch new transcripts using FIREFLIES_API_KEY; write markdown to Supabase storage/meetings; insert a metadata row into document_metadata.
   - Chunk and embed: for each new or changed transcript (by content_hash), chunk the transcript, compute embeddings, and upsert chunks into documents.
   - Project classification: determine likely project from participants, filename, and semantic cues; set document_metadata.project_id and phase='Current'. Use ML fallback when heuristic confidence < threshold.
   - Task/decision/risk extraction: generate structured entities from each transcript and create tasks in tasks table; attach decisions/risks as notes either in tasks metadata or a future decisions table (optional now, can embed in JSONB metadata).

4) Retrieval and reasoning
   - Implement a retriever that searches documents by hybrid filters (project_id, participants, recency) and vector similarity; add light LLM-based reranking on top-k.
   - Wrap the retriever behind agent tools so the chat agent can answer questions, cite sources, propose tasks, and summarize patterns.

5) Backend agent integration (Python Agents SDK)
   - Define agent tools:
     - fetch_related_chunks(query, project_id?, k): returns top-k chunks with metadata and citations.
     - classify_document(document_id): returns project_id and confidence; updates document_metadata.
     - extract_tasks(document_id): returns list of task objects; upserts into tasks.
     - summarize_meeting(document_id): returns executive summary, decisions, risks; stores in metadata.
     - generate_insights(project_id? or org-wide): returns insights derived from multi-meeting retrieval.
   - Expose HTTP endpoints consumed by the UI (e.g., /api/projects, /api/projects/:id, /api/chat, /api/ingest/fireflies/:id).

### Phase 2 — Project Intelligence Surfaces
Goal: surface the Phase 1 capabilities through new Next.js experiences and scoped chat entry points.

6) Frontend UI (Next.js)
   - Projects index page: table of projects with counts (meetings, open tasks) and last activity; link to project detail.
   - Project detail page: sections for associated meetings (from document_metadata), open tasks, and AI-generated insights; include an Ask about this project chat panel that scopes retrieval to project_id.
   - Global chat page: organization-wide Ask Alleato with RAG over all projects.

### Phase 3 — Reliability, Idempotence, and Ops
Goal: harden the system after UI + backend merge and certify handoff readiness.

7) Security, idempotence, and ops
   - Use content_hash to make ingestion idempotent. Upsert on unique keys (fireflies_id, content_hash, document_id+chunk_index).
   - RLS for Supabase tables for production; during local dev, use service role for backend scripts.
   - Add basic observability: ingestion logs and error handling with safe retries.

8) Validation
   - Run combined acceptance flows (ingestion → backend → UI) using seeded transcripts and sample projects.
   - Confirm RAG accuracy, classification, UI binding, and idempotence match the criteria in “Validation and Acceptance.”

9) Backend regression tests

    PYTHONPATH=python-backend python -m unittest \\
      python-backend.tests.test_fireflies_pipeline \\
      python-backend.tests.test_api_endpoints

   This command seeds the ingestion pipeline with the fixture transcript (dry-run) and exercises `/api/projects`, `/api/chat`, and `/api/ingest/fireflies` via FastAPI's TestClient. All tests must pass before continuing.

## Concrete Steps

All commands assume repository root as working directory unless noted.

### Phase 1 — RAG Chat Agent Setup

1) Bring up the demo unchanged

```
# 1. Discover directories (adjust if needed)
FRONTEND_DIR=$(ls -d */ | egrep -i 'web|ui|frontend|next|app' | head -n1)
BACKEND_DIR=$(ls -d */ | egrep -i 'server|api|backend|python|app' | head -n1)
echo $FRONTEND_DIR; echo $BACKEND_DIR

# 2. Back-end setup (Python)
cd "$BACKEND_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt || true  # if present
pip install openai supabase psycopg[binary] pydantic python-dotenv tiktoken
# Run the backend (adjust command per repo README)
python app.py || uvicorn app:app --reload || make run || echo "Start backend per repo"

# 3. Front-end setup (Next.js)
cd "../$FRONTEND_DIR"
npm install || pnpm install || yarn
npm run dev

# Visit local UI in browser and verify baseline chat works as in the original demo
```

2) Supabase schema (use SQL editor in Supabase dashboard or psql). Create extension and tables:

```
-- Enable pgvector (managed by Supabase)
create extension if not exists vector;
create extension if not exists pg_trgm; -- For better text search

-- Projects table
create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  description text,
  phase text not null default 'Current', -- 'Backlog', 'Current', 'Paused', 'Done'
  owners text[],
  participants text[],
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_projects_phase on public.projects(phase);

-- Document metadata for each meeting transcript
create table if not exists public.document_metadata (
  id uuid primary key default gen_random_uuid(),
  fireflies_id text unique,
  filename text,
  participants text[],
  captured_at timestamptz,
  summary text,
  full_text_url text, -- link to file in storage bucket
  content_hash text not null,
  project_id uuid references public.projects(id) on delete set null,
  phase text not null default 'Current',
  raw_text text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_document_metadata_project on public.document_metadata(project_id);
create unique index if not exists ux_document_metadata_fireflies on public.document_metadata(fireflies_id);
create index if not exists idx_document_metadata_captured_at on public.document_metadata(captured_at);

-- Meeting segments table (semantic sections within meetings)
create table if not exists public.meeting_segments (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.document_metadata(id) on delete cascade,
  segment_index int not null,
  segment_title text not null,
  segment_summary text,
  start_time int, -- seconds from meeting start
  end_time int,
  speaker_count int,
  decisions jsonb default '[]'::jsonb,
  risks jsonb default '[]'::jsonb,
  tasks jsonb default '[]'::jsonb,
  segment_embedding vector(3072), -- embedding of segment summary
  created_at timestamptz not null default now(),
  unique(document_id, segment_index)
);
create index if not exists idx_segments_document on public.meeting_segments(document_id);
create index if not exists idx_segments_embedding on public.meeting_segments using ivfflat (segment_embedding vector_cosine_ops) with (lists = 100);

-- Vectorized chunks table with enhanced metadata
create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.document_metadata(id) on delete cascade,
  segment_id uuid references public.meeting_segments(id) on delete cascade, -- NEW: link to segment
  chunk_id text not null,
  chunk_index int not null,
  token_count int,
  text text not null,
  embedding vector(3072) not null, -- text-embedding-3-large dimensions
  content_hash text not null,
  metadata jsonb not null default '{}'::jsonb,
  -- Enhanced metadata for improved RAG
  chunk_type text not null default 'content', -- 'content', 'summary', 'segment_summary', 'meeting_summary'
  semantic_density float, -- coherence score for chunk quality
  speaker_transitions int, -- number of speaker changes in chunk
  topic_keywords text[], -- extracted keywords for BM25
  speakers text[], -- list of speakers in this chunk
  created_at timestamptz not null default now()
);
create unique index if not exists ux_documents_doc_idx on public.documents(document_id, chunk_index);
create index if not exists idx_documents_segment on public.documents(segment_id);
create index if not exists idx_documents_hash on public.documents(content_hash);
create index if not exists idx_documents_gin on public.documents using gin (metadata);
create index if not exists idx_documents_embedding on public.documents using ivfflat (embedding vector_cosine_ops) with (lists = 100);
-- Add GIN index for full-text search (BM25 alternative)
create index if not exists idx_documents_fts on public.documents using gin(to_tsvector('english', text));
create index if not exists idx_documents_keywords on public.documents using gin(topic_keywords);

-- Tasks extracted by AI or humans
create table if not exists public.tasks (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete set null,
  source_document_id uuid references public.document_metadata(id) on delete set null,
  title text not null,
  description text,
  assignee text,
  status text not null default 'open',
  due_date date,
  created_by text not null default 'ai',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb
);
create index if not exists idx_tasks_project on public.tasks(project_id);
create index if not exists idx_tasks_assignee on public.tasks(assignee);
create index if not exists idx_tasks_status on public.tasks(status);

-- Decisions table (strategic intelligence)
create table if not exists public.decisions (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid references public.document_metadata(id) on delete cascade,
  segment_id uuid references public.meeting_segments(id) on delete set null,
  project_id uuid references public.projects(id) on delete set null,
  decision_text text not null,
  rationale text,
  decision_maker text,
  impact text, -- 'high', 'medium', 'low'
  status text default 'active', -- 'active', 'revised', 'obsolete'
  effective_date date,
  embedding vector(3072), -- embedding of decision_text
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_decisions_project on public.decisions(project_id);
create index if not exists idx_decisions_meeting on public.decisions(meeting_id);
create index if not exists idx_decisions_status on public.decisions(status);
create index if not exists idx_decisions_embedding on public.decisions using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Risks table (strategic intelligence)
create table if not exists public.risks (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid references public.document_metadata(id) on delete cascade,
  segment_id uuid references public.meeting_segments(id) on delete set null,
  project_id uuid references public.projects(id) on delete set null,
  risk_category text, -- 'technical', 'schedule', 'resource', 'client', 'regulatory'
  risk_description text not null,
  likelihood text, -- 'high', 'medium', 'low'
  impact text, -- 'high', 'medium', 'low'
  owner text,
  mitigation_plan text,
  status text default 'open', -- 'open', 'mitigating', 'accepted', 'closed'
  identified_date date,
  target_resolution_date date,
  embedding vector(3072), -- embedding of risk_description
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_risks_project on public.risks(project_id);
create index if not exists idx_risks_status on public.risks(status);
create index if not exists idx_risks_category on public.risks(risk_category);
create index if not exists idx_risks_embedding on public.risks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Opportunities table (strategic intelligence)
create table if not exists public.opportunities (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid references public.document_metadata(id) on delete cascade,
  segment_id uuid references public.meeting_segments(id) on delete set null,
  project_id uuid references public.projects(id) on delete set null,
  opportunity_type text, -- 'revenue', 'efficiency', 'process', 'partnership', 'innovation'
  description text not null,
  potential_value text,
  owner text,
  next_steps text,
  status text default 'identified', -- 'identified', 'evaluating', 'pursuing', 'captured', 'declined'
  embedding vector(3072), -- embedding of description
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_opportunities_project on public.opportunities(project_id);
create index if not exists idx_opportunities_type on public.opportunities(opportunity_type);
create index if not exists idx_opportunities_status on public.opportunities(status);
create index if not exists idx_opportunities_embedding on public.opportunities using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Commitments table (accountability tracking)
create table if not exists public.commitments (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid references public.document_metadata(id) on delete cascade,
  project_id uuid references public.projects(id) on delete set null,
  committed_by text not null,
  commitment_text text not null,
  committed_to text,
  due_date date,
  status text default 'pending', -- 'pending', 'in_progress', 'completed', 'overdue', 'cancelled'
  completed_date date,
  embedding vector(3072), -- embedding of commitment_text
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_commitments_project on public.commitments(project_id);
create index if not exists idx_commitments_committed_by on public.commitments(committed_by);
create index if not exists idx_commitments_status on public.commitments(status);
create index if not exists idx_commitments_due_date on public.commitments(due_date);

-- Query cache table for performance
create table if not exists public.query_cache (
  id uuid primary key default gen_random_uuid(),
  query_hash text not null unique,
  query_text text not null,
  query_embedding vector(3072),
  results jsonb not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '15 minutes'
);
create index if not exists idx_query_cache_expires on public.query_cache(expires_at);

-- Evaluation metrics table
create table if not exists public.rag_metrics (
  id uuid primary key default gen_random_uuid(),
  query_id text,
  metric_type text not null, -- 'faithfulness', 'relevance', 'context_precision', 'context_recall'
  score float not null,
  metadata jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_rag_metrics_type on public.rag_metrics(metric_type);

-- Storage bucket for meetings (create in Supabase Storage UI or via API)
-- Name: meetings
```

3) Environment configuration

```
# Create .env files
cat > .env << 'EOF'
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
FIREFLIES_API_KEY=...
EOF

# Frontend .env.local (Next.js)
cat > "$FRONTEND_DIR"/.env.local << 'EOF'
NEXT_PUBLIC_SUPABASE_URL=https://<your-project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
OPENAI_API_KEY=sk-...
EOF
```

4) Ingestion pipeline (scripts and backend integration)

The MVP ingestion path now lives at `python-backend/ingestion/fireflies_pipeline.py` and is wired to `/api/ingest/fireflies`. It parses markdown exports, hashes content, chunks text, generates embeddings (real or hashed fallback), and upserts metadata/chunks/tasks/insights through `SupabaseRagStore`. The following checklist captures enhancements that still need to land on top of that foundation:

- Create a Python script at scripts/ingest_fireflies.py to:
  - Fetch transcripts via FIREFLIES_API_KEY (by date range or list of IDs).
  - Normalize to markdown, compute content_hash (sha256 of normalized text).
  - Upload file to Supabase storage bucket meetings at path YYYY/MM/<fireflies_id>.md.
  - Upsert into document_metadata by fireflies_id or content_hash.
  - Run chunk_and_embed(text, document_id) to produce chunks and insert into documents.
  - Call classify_document(document_id) to set project_id and phase.
  - Call extract_tasks(document_id) to populate tasks.

- Suggested function signatures (in backend Python module, e.g., BACKEND_DIR/alleato/ingest.py):

```
def compute_content_hash(text: str) -> str: ...

# NEW: Segmentation-first approach
def segment_meeting_with_llm(transcript_text: str, meeting_id: str) -> list[dict]:
    """Use LLM to identify 5-10 semantic segments in meeting transcript.
    Returns: [{
        segment_index: int,
        segment_title: str,  # e.g., "Budget Discussion"
        segment_summary: str,  # 3-5 sentence summary
        start_time: int,  # seconds from start
        end_time: int,
        speakers: list[str],
        decisions: list[dict],  # extracted decisions
        risks: list[dict],  # identified risks
        tasks: list[dict]  # action items
    }]
    """

def chunk_within_segment(segment_text: str, segment_id: str, segment_boundaries: tuple) -> list[dict]:
    """Create chunks WITHIN a single segment (never cross boundaries).
    Returns: [{
        chunk_index: int,
        segment_id: str,  # links to parent segment
        text: str,
        token_count: int,
        speakers: list[str],
        semantic_density: float,
        topic_keywords: list[str],
        speaker_transitions: int
    }]
    """

def extract_structured_entities(segment_data: dict, meeting_id: str, project_id: str) -> dict:
    """Extract and structure decisions, risks, opportunities, commitments.
    Returns: {
        'decisions': [{
            'text': str, 'rationale': str, 'impact': str,
            'owner': str, 'embedding': vector
        }],
        'risks': [{
            'description': str, 'category': str, 'likelihood': str,
            'impact': str, 'mitigation': str, 'embedding': vector
        }],
        'opportunities': [{
            'description': str, 'type': str, 'value': str,
            'next_steps': str, 'embedding': vector
        }],
        'commitments': [{
            'who': str, 'what': str, 'to_whom': str,
            'by_when': date, 'embedding': vector
        }]
    }
    """

def classify_query(query: str) -> str:
    """Classify query for optimal retrieval routing.
    Returns: 'fact_lookup'|'status_check'|'pattern_analysis'|
             'risk_assessment'|'strategic_planning'
    """

def two_stage_retrieval(query: str, query_type: str, project_id: str = None) -> dict:
    """Sophisticated two-stage retrieval pipeline.
    Stage 1: Find relevant meetings (search meeting/segment summaries)
    Stage 2: Retrieve chunks ONLY from those meetings
    Returns: {
        'meeting_ids': list[str],  # Selected meetings from Stage 1
        'chunks': list[dict],  # Retrieved chunks from Stage 2
        'decisions': list[dict],  # Related structured data
        'risks': list[dict],
        'opportunities': list[dict],
        'confidence_scores': list[float]
    }
    """

def synthesize_strategic_response(retrieved_data: dict, query: str) -> dict:
    """Transform retrieval into strategic intelligence.
    Returns: {
        'direct_answer': str,
        'patterns': list[dict],  # Detected patterns across meetings
        'root_causes': list[str],  # Analyzed root causes
        'impacts': list[dict],  # Assessed impacts
        'recommendations': list[dict],  # Strategic recommendations
        'evidence': list[dict],  # Supporting citations
        'confidence': float,
        'follow_ups': list[str]  # Suggested next questions
    }
    """
```

- Segment-First Chunking Strategy (Critical for Strategic Intelligence):

  a) Meeting Preprocessing:
     - Strip boilerplate headers/footers from transcript
     - Normalize speaker names consistently throughout
     - Extract timestamps and convert to seconds from start
     - Identify any explicit agenda items or section markers

  b) LLM-Based Semantic Segmentation (NEW - First Pass):
     - Use GPT-4 to analyze entire transcript and identify 5-10 semantic segments
     - Each segment represents a distinct topic/agenda item (e.g., "Budget Discussion", "Technical Issues", "Next Steps")
     - For each segment, extract:
       * segment_title: Descriptive name of the topic
       * start_time/end_time: Temporal boundaries
       * segment_summary: 3-5 sentence summary
       * decisions: List of decisions made in segment
       * risks: Risks identified in segment
       * tasks: Action items from segment
     - Store in meeting_segments table with segment embedding

  c) Chunk Within Segments (Second Pass):
     - ONLY chunk within segment boundaries (never across)
     - Target size: 800-1200 tokens per chunk
     - Overlap: 150 tokens (but never cross segment boundary)
     - Preserve speaker turns when possible
     - Calculate semantic density using embedding similarity
     - Each chunk links to parent segment_id

  d) Multi-Resolution Embeddings:
     - Meeting-level: Embed entire meeting summary → document_metadata
     - Segment-level: Embed each segment summary → meeting_segments
     - Chunk-level: Embed actual content → documents
     - Entity-level: Embed decisions/risks/opportunities → respective tables

  e) Metadata Enrichment:
     - Extract keywords using TF-IDF for each chunk
     - Count speaker transitions
     - Identify key entities (people, projects, companies)
     - Tag with project_id based on classification

5) Advanced Two-Stage Retrieval and RAG Pipeline

- Query Classification (Route to Optimal Strategy):
  ```python
  def classify_query(query: str) -> QueryType:
      # Use regex patterns or lightweight LLM to classify:
      # - 'fact_lookup': "When did X happen?", "What did Y say about Z?"
      # - 'status_check': "Where are we with X?", "What's the status of Y?"
      # - 'pattern_analysis': "What trends...", "Recurring issues..."
      # - 'risk_assessment': "What risks...", "What could go wrong..."
      # - 'strategic_planning': "How should we...", "What's our strategy..."
      return query_type
  ```

- Two-Stage Retrieval Pipeline (Meeting-First Approach):

  a) Stage 1 - Meeting Selection (Precision Focus):
     - Based on query_type, search different embeddings:
       * fact_lookup → meeting_segments + documents
       * risk_assessment → risks table + meeting summaries
       * strategic_planning → decisions + opportunities + meeting summaries
     - Apply metadata filters: project_id, date_range, participants
     - Use cosine similarity on meeting/segment embeddings
     - Select top 20-30 relevant meetings
     - This dramatically reduces search space from thousands to dozens

  b) Stage 2 - Chunk Retrieval (Within Selected Meetings):
     - Search ONLY within meeting_ids from Stage 1
     - Hybrid search combining:
       * Dense vectors (0.7 weight): embedding similarity
       * BM25/FTS (0.3 weight): keyword matching
     - Reciprocal Rank Fusion: score = 0.7/(vector_rank+60) + 0.3/(keyword_rank+60)
     - Apply temporal decay: score * 0.95^(months_old)
     - Retrieve top 100 candidates

  c) Multi-Stage Reranking:
     - Cross-encoder rerank: top-100 → top-30 (semantic understanding)
     - MMR rerank: top-30 → top-8 (diversity with λ=0.5)
     - Ensures diverse perspectives across different meetings
     - Prevents single meeting from dominating results

  d) Structured Knowledge Integration:
     - Pull related decisions, risks, opportunities for context
     - Join to source segments for additional detail
     - Merge structured + unstructured results

- Implement Caching Strategy:
  - Query cache: Store results with 15-minute TTL
  - Embedding cache: Cache frequently accessed chunk embeddings
  - Invalidate on new document ingestion
  - Monitor cache hit rates for optimization

- Provide Enhanced Agent Tools:
  - fetch_related_chunks: Standard retrieval with formatting
  - fetch_temporal_context: Chronological meeting progression
  - fetch_cross_project_patterns: Pattern detection across projects
  - evaluate_retrieval_quality: Compute RAGAS metrics for result set

6) Strategic Synthesis Layer (Transform Retrieval → Intelligence)

This layer transforms raw retrieval into strategic insights:

```python
def synthesize_strategic_response(query: str, retrieved_data: dict) -> dict:
    """
    Takes retrieved chunks + structured knowledge and produces strategic analysis.
    This is where the system becomes a 'thinking partner' not a search engine.
    """

    # Step 1: Pattern Detection
    patterns = detect_patterns(retrieved_data)
    # - Recurring themes across meetings
    # - Common risks across projects
    # - Decision evolution over time
    # - Bottlenecks and blockers

    # Step 2: Root Cause Analysis
    root_causes = analyze_root_causes(patterns)
    # - Why are delays happening repeatedly?
    # - What drives consistent successes?
    # - Where do breakdowns occur?

    # Step 3: Impact Assessment
    impacts = assess_impacts(retrieved_data)
    # - Which decisions had positive outcomes?
    # - What risks materialized?
    # - Which opportunities were missed?

    # Step 4: Strategic Recommendations
    recommendations = generate_recommendations(
        patterns, root_causes, impacts
    )
    # - Process improvements
    # - Resource reallocations
    # - Risk mitigation strategies
    # - Growth opportunities

    # Step 5: Format Strategic Response
    return {
        'direct_answer': answer,  # Answers the question
        'analysis': {            # Provides deeper insight
            'patterns': patterns,
            'root_causes': root_causes,
            'impacts': impacts
        },
        'recommendations': recommendations,
        'evidence': citations,   # Source backing
        'confidence': score,
        'follow_ups': questions  # Proactive next questions
    }
```

The synthesis layer ensures every response includes:
- Direct answer to the question
- Pattern analysis across time/projects
- Root cause identification
- Strategic recommendations
- Evidence-based citations
- Confidence scoring
- Proactive follow-up questions

7) Backend Agent Tools and HTTP Endpoints

- Add endpoints (FastAPI or Flask) to the Python backend:
  - GET /api/projects — list projects with counts (meetings, open tasks).
  - GET /api/projects/:id — details + latest insights + associated meetings and open tasks.
  - POST /api/chat — body: {message, project_id?}; response: {reply, sources[], followups[]}.
  - POST /api/ingest/fireflies — body: {ids?: string[], since?: ISODate}; triggers ingestion.

- Implement the agent using the Agents SDK and register tools: classify_document, extract_tasks, summarize_meeting, fetch_related_chunks, generate_insights. Tool calls update Supabase.

### Phase 2 — Project Intelligence Surfaces

7) Frontend changes (Next.js)

- Add a Projects page at /projects showing a table: Project, Phase, Meetings, Open Tasks, Last Activity. Link to /projects/[id].
- Add a Project page at /projects/[id] with:
  - Meetings list (from document_metadata where project_id = id) with summaries and links to source files.
  - Open tasks (tasks where project_id=id and status='open').
  - AI Insights panel with refreshed insights via /api/projects/:id.
  - A chat panel scoped to the project: send {message, project_id} to /api/chat.
- Update global chat to default to org-wide but allow narrowing to a project.

### Phase 3 — Reliability, Idempotence, and Ops

8) Validation

- Seed: ingest 1–3 sample Fireflies transcripts and one existing projects row.
- Verify:
  - document_metadata row created per transcript; storage file exists; documents rows populated with ~800–1200 token chunks.
  - classification sets project_id with reasonable confidence; phase is 'Current'.
  - tasks created with sensible titles and descriptions.
  - RAG answers project questions citing sources; recency and project filters work.
  - UI pages render Projects index and Project detail with correct counts and data.

## Validation and Acceptance

Acceptance is defined as behaviors a human can verify end-to-end:

- Starting the backend and frontend locally, user can ingest at least one transcript via POST /api/ingest/fireflies with a Fireflies ID or by dropping a local markdown file for dev; the system writes a storage object in bucket meetings and creates a document_metadata row with a non-empty summary and content_hash.
- Navigating to /projects shows at least one project with accurate meeting and open task counts; clicking /projects/<id> shows open tasks and insights returned by `/api/projects/{id}`.
- Using the chat with a question like "What are the biggest risks and open decisions for Project X this quarter?" returns an answer with 3–8 citations linking back to transcript chunks.
- Creating an ad-hoc question like "List commitments Alice made in the last 2 weeks" yields a result with sources and optional follow-up tasks created in tasks.
- Re-running ingestion on the same transcript does not duplicate rows (idempotent upserts by content_hash and (document_id, chunk_index)).
- Backend regression suite `PYTHONPATH=python-backend python -m unittest python-backend.tests.test_fireflies_pipeline python-backend.tests.test_api_endpoints` passes without failures.

### RAG Quality Metrics (Target Thresholds)

**Retrieval Performance:**
- P95 latency < 1.5s for project-scoped queries (with cache)
- P95 latency < 3s for org-wide queries (without cache)
- Cache hit rate > 40% after warm-up period

**RAGAS Metrics** (evaluated on test set of 50 queries):
- Faithfulness: > 0.85 (answers grounded in retrieved context)
- Answer Relevance: > 0.80 (answers address the query)
- Context Precision: > 0.75 (retrieved chunks are relevant)
- Context Recall: > 0.70 (important information is retrieved)

**Hybrid Search Effectiveness:**
- Proper noun recall (names, projects): > 90%
- Acronym/terminology recall: > 85%
- Topic coverage (diverse results): MMR diversity score > 0.6

**Chunking Quality:**
- Average semantic density score > 0.7
- Speaker transition preservation > 95%
- Topic boundary detection accuracy > 80%

## Idempotence and Recovery

- Use content_hash (sha256 of normalized text) to detect changes and skip reprocessing when unchanged.
- Upsert documents on unique key (document_id, chunk_index); delete-orphan strategy: if a transcript is re-chunked, mark old chunks for deletion after successful insert of new chunks.
- If embedding fails mid-run, record a transient status in metadata and allow safe re-run; scripts are restartable and can be scheduled.
- Provide a dry-run mode for ingestion that only prints intended mutations.

## Artifacts and Notes

- Example ingestion log (abridged):

```
fetched fireflies_id=FF-12345; participants=["Alice","Bob"]; captured_at=2024-11-10T15:00Z
uploaded storage path: meetings/2024/11/FF-12345.md; bytes=182,334
content_hash=0x9c2b... upserted document_metadata id=2b2f...
chunked: 27 chunks (avg 1034 tokens, overlap 150); embedding model=text-embedding-3-large
upserted 27 chunks; classify → project_id=8f1a..., confidence=0.84
extracted tasks: 3 created, 1 updated
```

- Example retriever SQL (conceptual):

```
select d.*, dm.filename, dm.captured_at
from documents d
join document_metadata dm on dm.id = d.document_id
where (dm.project_id = $1 or $1 is null)
order by 1 - (d.embedding <=> $query_embedding) limit 50;
```

- Prompting notes: prefer system prompts that enforce citation of document_id+chunk_index and warn against fabrications; use reranking for diversity across meetings.

## Interfaces and Dependencies

- Python backend dependencies: openai, supabase, psycopg[binary], fastapi or flask, pydantic, tiktoken.
- Next.js frontend dependencies: @supabase/supabase-js, SWR/React Query for data fetching, Chat UI components already present.
- Supabase features: Storage (bucket meetings), Postgres (projects, document_metadata, documents, tasks), pgvector (embedding index). Dimension of vector must match chosen embedding model (e.g., 3072 for text-embedding-3-large).

Key function and endpoint contracts:

```
# Backend Python module alleato/rag.py

def hybrid_retriever(query: str, project_id: str | None, k: int = 8, use_cache: bool = True) -> list[dict]:
    """Advanced hybrid retrieval with query expansion, RRF fusion, and MMR reranking.
    Returns: [{chunk_id, text, score, document_id, filename, snippet, confidence, metadata}]
    """

def query_expansion(query: str, expansion_type: str = 'auto') -> dict:
    """Expand query using HyDE, synonyms, or entity extraction.
    Returns: {original: str, expanded: list[str], entities: list[str], keywords: list[str]}
    """

def mmr_rerank(candidates: list[dict], query_embedding: list[float], lambda_param: float = 0.5, k: int = 8) -> list[dict]:
    """Maximal Marginal Relevance reranking for diversity."""

def cross_encoder_rerank(query: str, candidates: list[dict], top_k: int = 30) -> list[dict]:
    """Cross-encoder reranking using sentence-transformers."""

def compute_rag_metrics(query: str, context: list[str], answer: str) -> dict:
    """Compute RAGAS metrics for quality evaluation.
    Returns: {faithfulness: float, relevance: float, context_precision: float, context_recall: float}
    """

# Backend HTTP endpoints

GET  /api/projects              → {projects: [{id, name, phase, meeting_count, open_task_count, last_activity}]}
GET  /api/projects/:id          → {project: {...}, meetings: [...], tasks: [...], insights: [...]}
POST /api/chat                  → {reply, sources: [...], followups: [...], metrics: {...}}
POST /api/ingest/fireflies      → {ingested: n, skipped: m, errors: [...], chunks_created: n}
GET  /api/metrics/rag           → {avg_faithfulness: float, avg_relevance: float, queries_evaluated: n}

# Supabase schema: see SQL above. Ensure vector index created and tuned.
# Redis cache: Configure for embedding and query result caching with appropriate TTL.
```

## Critical Success Factors

The success of this system depends on:
1. **Segmentation Quality**: LLM-based meeting segmentation must accurately identify topic boundaries
2. **Structured Knowledge Extraction**: Decisions, risks, and opportunities must be extracted with high precision
3. **Two-Stage Retrieval**: Meeting-first retrieval dramatically improves precision
4. **Strategic Synthesis**: The system must provide insights and recommendations, not just search results
5. **Multi-Resolution Architecture**: Meeting → Segment → Chunk hierarchy enables better context understanding

## Key Differentiators from Simple RAG

This is NOT a basic RAG system. It's a strategic intelligence platform that:
- **Thinks**: Performs pattern analysis and root cause detection
- **Remembers**: Maintains structured knowledge, not just text
- **Advises**: Provides strategic recommendations based on patterns
- **Learns**: Builds institutional knowledge over time
- **Acts**: Creates tasks, tracks commitments, identifies opportunities

Maintenance note: Keep this ExecPlan updated as code lands. Every time you choose specific file paths, record them here so a future contributor can resume from this document alone.

Plan Update (2025-12-05 12:30Z): Documented completed Phase 1 tasks (Supabase schema regeneration, ingestion pipeline, REST endpoints, tests, and project UI), recorded schema-related surprises/decisions, and added regression testing guidance.
