# Plan - AI Project Manager

The goal of this agent is to function as the company’s AI Chief of Staff — an executive-level system that continuously ingests institutional knowledge, synthesizes insights, and proactively drives strategic execution across every project and division.

This is the foundation of the first AI-native company brain — an agent that elevates the organization’s intelligence, speed, and strategic execution far beyond what is possible with human memory alone.

Instead of acting like a simple knowledge retrieval bot, this agent becomes the central intelligence layer of the business, capable of:

- Understanding the full history of the company
- Detecting patterns, risks, and opportunities across years of meetings
- Providing strategic guidance to leadership
- Tracking commitments, decisions, and tasks
- Ensuring follow-through and accountability
- Supporting team members through a conversational interface
- Becoming the “memory” and “thinking partner” of the entire organization

## What the Agent Is Designed to Do

### 1. Absorb Every Meeting the Company Has Ever Had

Every meeting transcript (Fireflies export) is automatically ingested into Supabase, segmented, chunked, embedded, and distilled into structured knowledge. The agent ultimately knows everything—and remembers it better than any employee ever could.

- Tasks
- Risks
- Decisions
- Opportunities
- Themes
- Project relationships
- People relationships

### 2. Develop Situational Awareness Across All Projects

By storing structured meeting intelligence It becomes the “single source of truth” for what is actually happening inside the business. The agent can:
- Track the progression of each project through time
- Analyze what has changed since the last meeting
- Identify blockers, repeated mistakes, or patterns
- Compare performance across clients, teams, and divisions
- Highlight execution gaps or unaddressed risks

### 3. Transform Conversations Into Strategy

The agent doesn’t just store information. It thinks:
- Synthesizes insights
- Identifies root causes
- Spots systemic issues
- Projects outcomes
- Makes recommendations

It answers not with citations—but with strategic guidance, shaped by everything it has consumed. When leadership asks a complex question (“Where are we losing weeks in our ASRS engagements?”), the agent pulls patterns across dozens of meetings and returns a high-level analysis, not a search result.

### 4. Create Company-Wide Accountability

Because the agent extracts tasks, decisions, and commitments, it can:
- Track whether commitments were fulfilled
- Detect when deadlines are slipping
- Surface unresolved risks
- Remind owners when tasks go stale

### 5. Provide a Powerful Chat Interface For the Entire Team

Any team member can ask:
- “What are the outstanding tasks for Project X?”
- “What risks do we have with Client Y right now?”
- “What did we decide about ASRS design on Monday?”
- “Are there any opportunities we’re missing in permitting?”

The agent responds using RAG + internal reasoning + structured data to answer with clarity, context, and actionable insight.

### 6. Become a Proactive Partner for Leadership

Ultimately, the agent becomes capable of:
- Proactively alerting leadership to risks
- Summarizing the week’s activity
- Suggesting process improvements
- Identifying talent bottlenecks
- Proposing strategic initiatives
- Continuing to learn as more meetings occur

This positions the agent not as a tool, but as a thinking partner — an always-awake, always-prepared strategist with total recall and pattern-matching abilities that exceed any human.

The Vision: A Self-Learning Operating System for the Business

This system becomes the nucleus for a future state where:
- Every project has an AI project manager
- Every meeting updates the company brain
- Every employee has an AI assistant
- Leadership gets automated insights
- Execution is tracked autonomously
- Institutional memory is permanent
- Decisions compound instead of being lost

## RAG STRATEGY

### A. Chunking Strategy

#### 1) Treat each meeting as a “session” with layered artifacts

For every Fireflies transcript, don’t just save “raw text”.

Create these layers per meeting:
	1.	Raw transcript (full text) – stored in Supabase storage.
	2.	Meeting-level metadata + summary – in document_metadata:
- fireflies_id
- date/time, duration
- participants
- project(s) / client(s) / tags
- high-level summary (LLM-generated)
- key decisions (bullets)
- key risks / issues
- list of action items
- themes (e.g., “staffing”, “ASRS design”, “client X launch”)
	3.	Segment-level chunks – in documents table:
- These are what you embed for RAG.

Think “episodic memory” (chunks) + “semantic memory” (summaries, decisions, risks).

#### 2) First split transcripts into semantic segments

Do NOT just naively chop every 500 tokens.

For each transcript, run a pre-processing step with an LLM to create segments:
- Split by:
- Agenda items (if present)
- Big topic shifts
- Natural phases: “opening / status update / problem discussion / options / decision / next steps”
- For each segment, store:
- segment_title (e.g., “Discussing Client X ASRS schedule delay”)
- start_time, end_time (or utterance indices)
- segment_summary (5–10 bullet summary)
- decisions_in_segment
- risks_in_segment
- tasks_in_segment

You can store these in a meeting_segments table or fold them into your documents table with a segment_id and some JSONB metadata.

This gives you:
- A structured hierarchy: meeting → segment → chunks.
- Better context for the embeddings.

#### 3) Chunk inside segments with sentence / speaker awareness

Within each segment, create token-based chunks, but keep them aligned to speaker turns and sentences.

Recommended:
- Model context: assume 8k+ tokens available.
- Chunk size: 600–900 tokens per chunk.
- Overlap: 100–150 tokens.
- Always break on sentence or speaker boundaries (never mid-sentence if you can avoid it).

Why this size?
- Smaller chunks (100–200 tokens) are too “thin” for nuanced strategy.
- Very large chunks (1500–2000) dilute similarity and pull too much irrelevant context.
- 600–900 with light overlap is a good balance for “mini-stories” of conversation.

Each chunk row in documents might look like:
- id
- metadata_id (FK to document_metadata)
- segment_id
- chunk_index
- content (the actual text for RAG)
- embedding (vector)
- meeting_date
- participants
- projects / client_ids (array)
- tags (themes, e.g., [“schedule”, “risk”, “ASRS”])

#### 4) Embed multiple “views” per meeting: chunks + summaries

For each meeting, create several embeddings, not just per chunk:
	1.	Chunk embeddings (as above) – granular recall.
	2.	Segment_summary embeddings – use segment_summary text as a “distilled embedding” for that segment.
	3.	Meeting_summary embedding – whole-meeting summary.

You can store these in either:
- Same documents table with doc_type = ‘chunk’ | ‘segment_summary’ | ‘meeting_summary’, or
- Separate tables for clarity.

This gives you a multi-resolution vector space:
- Meeting-level embeddings → “which meetings matter?”
- Segment-level embeddings → “which part of that meeting?”
- Chunk-level embeddings → “exact quotes and details.”

#### 5) Build distilled, structured knowledge tables (critical for “strategist”)

If you want this to act like a strategist, you need more than raw text.

Run an offline pipeline over transcripts to extract:
- Decisions → decisions table
- decision_id, project_id, meeting_id, date, description, rationale, owner, impact, status.
- Risks → risks table
- risk_id, project_id, meeting_id, risk_category, description, likelihood, impact, owner, mitigation_plan, status.
- Tasks / Action Items → tasks table
- task_id, meeting_id, project_id, assigned_to, due_date, priority, status, source_chunk_id.
- Ideas / Opportunities → opportunities table
- idea_id, project_id, type (revenue, efficiency, process), description, owner, next_step.

For each row, store:
- A short canonical text (e.g., “Implement standardized ASRS design checklist to cut permitting errors by 30%.”)
- An embedding for that text.

Now your agent can retrieve not only “what was said” but “what was decided / risky / assigned.”

This is where the “ultimate PM and strategist” actually comes from.

### B. Retrieval Strategy

You want retrieval that behaves differently depending on the query type and leans on both:
- Episodic memory (chunks and segments)
- Structured knowledge (decisions, risks, tasks, opportunities)

Think in terms of a multi-step retrieval pipeline.

#### 1) Classify the query and choose a retrieval plan

On each user query or internal “thinking” step, do an initial classification:
- Is this:
- Fact lookup? (“When did we agree to hire a second PM?”)
- Status / progress? (“Where are we with Project X ASRS installation?”)
- Pattern / trend? (“What are recurring issues with integrator partners?”)
- Risk / opportunity analysis? (“What are the top risks for Q1 in ASRS projects?”)
- Strategy / planning? (“How should we restructure our project management process?”)

Use that classification to:
- Decide which tables to prioritize.
- Decide how much emphasis to put on high-level vs low-level retrieval.

#### 2) Stage 1: Candidate meetings via high-level embeddings + metadata filters

Don’t immediately query all chunks. First, select relevant meetings.

Use a query like:
	1.	Use metadata filters when available:
- Filter by project_id, client_id, participants, date_range based on query.
	2.	Run vector search primarily over:
- meeting_summary embeddings
- segment_summary embeddings
- decisions, risks, tasks, opportunities embeddings

From this, you:
- Get a set of candidate meetings (and maybe specific segments).
- Limit to e.g. top 20 meetings.

This is fast and aligns retrieval to the right episodes.

#### 3) Stage 2: Fine-grained chunk retrieval within candidate meetings

Once you have candidate meetings/segments, run a second vector search over:
- chunk embeddings where metadata_id IN candidate_meetings.

Use:
- Top k per meeting: e.g., 3–5 best chunks per meeting.
- Max overall chunks: e.g., 20–30 total.

Apply MMR (Max Marginal Relevance) or a diversity heuristic so you don’t pull 10 variants of the same conversation moment.

#### 4) Blend structured + unstructured retrieval

For higher-order questions, prioritize structured tables:

Examples:
- “Where are our biggest risks?” → primary retrieval from risks table; supporting context from chunks.
- “What decisions led to cost overruns?” → primary retrieval from decisions + risks; then fetch source chunks for explanation.
- “What should we improve in project management?” → query risks, tasks, opportunities, and segment_summaries tagged with “process”, “bottleneck”, etc.

Rough strategy:
	1.	Run embedding search across decisions, risks, tasks, opportunities.
	2.	Collect the top N items from each (say N=10–20).
	3.	For each selected item, join to:
- meeting_id
- project_id
- source_chunk_id
	4.	Pull the source chunks only for a subset (e.g., top 5–10) to keep context compact.

This gives you: “Here are the structured objects that matter + the actual conversation behind them.”

#### 5) Time-aware and participant-aware scoring

Layer in additional scoring:
- Recency:
- Slight time decay factor: older items still matter but are slightly downweighted unless the query explicitly mentions a timeframe.
- Participant relevance:
- If the query is from or about a specific person, give extra weight to transcripts where they were a participant.
- Project relevance:
- If the query mentions a project/client (“Hy-Tek”, “Alleato ASRS”), heavily prioritize those.

You can implement this as:
- similarity_score * w1 + recency_score * w2 + participant_match * w3 + project_match * w4

And sort on a combined score.



#### 6) Aggregation + synthesis pass (where the “strategist” shows up)

Once you have retrieved:
- A set of chunks
- A set of decisions/risks/tasks/opportunities
- A list of relevant meetings/projects

You do NOT just stuff them into the prompt and say “answer this.”

You ask the model to:
	1.	First, internally summarize and cluster:
- Group decisions by project and theme.
- Group risks by category.
- Identify recurring patterns (“ASRS schedule risk due to permitting” appearing in 5 meetings).
	2.	Then answer the user with:
- A synthesized viewpoint (“Here’s what’s actually going on.”)
- Supported by references (“This is based on decisions from X, Y, and risks R1, R2.”)
- Concrete recommendations and next steps.

In other words, retrieval gives signals and evidence; the generation step performs analysis and strategy, not regurgitation.



#### 7) Conversational RAG for the chat interface

For the live chat with team members:
- Maintain a conversation-level working memory:
- A short rolling summary of the last N turns.
- A set of “open threads” (unresolved tasks, questions) in the conversation.

On each new message:
	1.	Combine:
- User question
- Conversation summary
- User identity (role, department)
- Optional project context (if the chat is “inside” a project view)
	2.	Run the two-stage retrieval pipeline.
	3.	Answer with:
- Immediate answer to their question.
- Optional additional strategic insight (“By the way, this connects to previous risk XYZ.”)
- Option to propose tasks or follow-ups (which can be written back to your tasks table or another PM system).



C. How this becomes a “high-level business strategist” instead of a search bot

**Key points that make this system strategic:**

1.	Multi-layer knowledge:
- Transcript chunks (episodic memory).
- Meeting/segment summaries.
- Structured tables for decisions, risks, tasks, opportunities.
- Periodic “roll-up” docs (quarterly reviews, project health summaries) you can generate offline and embed as well.

2.	Pattern-focused retrieval:
- Not just “find me where this sentence occurred.”
- “Show me all risks tagged ‘permitting’ in ASRS projects over last 12 months.”
- “Cluster common themes in complaints about integrators.”

3.	Synthesis-first answering:
- Use retrieved content as raw material.
- Ask the model to analyze: root causes, recurring patterns, systemic issues.
- Then have it propose strategies: process changes, KPIs, org changes, experiment ideas.

4.	Feedback loop / learning over time:
- Each time leadership asks a big question and likes the answer:
- Store that Q & A pair as a “strategic memo” with its own embedding.
- Over time you build a library of:
- “Company doctrines”
- “Standard operating strategies”
- New answers can leverage that library to stay consistent and get sharper.

## INGESTION PIPELINE

### 1. Overall Architecture

Goal: For every Fireflies meeting, you end up with:

- Raw transcript (and optional audio) in Supabase Storage
- A row in document_metadata summarizing the meeting
- Multiple rows in documents (segments + chunks + summaries) with embeddings
- Structured rows in decisions / risks / tasks / opportunities with embeddings

High-level flow:
	1.	Discover new / updated Fireflies meetings
	2.	Fetch transcript + metadata
	3.	Store transcript file in Supabase storage
	4.	Upsert document_metadata row
	5.	Run LLM “segmenter” to create semantic segments
	6.	Chunk segments into vector chunks
	7.	Run embeddings and insert into documents
	8.	Run LLM “extractor” to create decisions, risks, tasks, opportunities
	9.	Embed and insert into corresponding tables

This can run as:
- A scheduled job (cron / n8n / Supabase Edge Function / Cloudflare Worker)
- - optional Fireflies webhooks for near-real-time ingestion

### 2. Stage 0–3: Fireflies → Supabase Storage + document_metadata

### Stage 0: Prerequisites

- Supabase:
- Storage bucket: meeting-transcripts (or similar)
- Tables:
- document_metadata (already planned)
- documents (for embeddings)
- Structured tables (we’ll use later)
- Environment:
- FIRELIES_API_KEY
- OPENAI_API_KEY (or other LLM/embedding provider)
- Supabase service key for server-side worker

#### Stage 1: Discover new or updated Fireflies meetings

You want two modes:
	1.	Backfill:
- One-time script: fetch all meetings from last 3+ years in pages
- Store their fireflies_id and ingestion status
	2.	Incremental:
- Either:
- Poll Fireflies API every X minutes for meetings since last_ingested_timestamp, or
- Use Fireflies webhook → your endpoint → push job to queue

Pseudo-code (Node/Python style):

def discover_meetings(since_timestamp):
    resp = fireflies.get_meetings(updated_after=since_timestamp)
    for meeting in resp.meetings:
        enqueue_ingestion_job(meeting['id'])

You keep a simple fireflies_ingestion_jobs table or queue to track what’s pending, in-progress, failed.

Stage 2: Fetch transcript + metadata

For each fireflies_id job:
- Call Fireflies API:
- Get:
- transcript text (full)
- participants (names, emails)
- meeting title
- start time / end time
- tags or topics if Fireflies provides them
- any built-in summary / action items (you can still override/improve, but it’s useful context)

Represent as a local object:

```
{
  "fireflies_id": "ff_123",
  "title": "ASRS Coordination w/ Hy-Tek",
  "started_at": "2025-11-30T14:00:00Z",
  "ended_at": "2025-11-30T15:00:00Z",
  "participants": [
    {"name": "Brandon", "email": "brandon@..."},
    {"name": "Hy-Tek PM", "email": "pm@hy-tek.com"}
  ],
  "transcript_text": "... full text ...",
  "fireflies_summary": "...",
  "fireflies_actions": ["...", "..."]
}
```

#### Stage 3: Save transcript in Supabase Storage + upsert document_metadata

3.1. Storage upload
- Path convention (deterministic, idempotent):
meeting-transcripts/{year}/{month}/{fireflies_id}.txt

Example:

path = f"{started_at.year}/{started_at.month:02d}/{fireflies_id}.txt"
supabase.storage.from_("meeting-transcripts").upload(path, transcript_text.encode("utf-8"), upsert=True)

Store the resulting storage_path or public URL.

3.2. Upsert document_metadata

document_metadata (minimal useful columns for this pipeline):
- id (uuid / bigserial)
- fireflies_id (text, unique)
- title
- started_at, ended_at
- participants (jsonb or text[])
- storage_path (text)
- fireflies_summary (text)
- fireflies_actions (jsonb or text[])
- status (text: ‘raw_ingested’ | ‘segmented’ | ‘chunked’ | ‘embedded’ | ‘structured_extracted’ | ‘error’)
- last_processed_at
- project_id or client_id (nullable FK; you can infer later)
- themes (text[] tags like [“ASRS”, “permitting”, “Hy-Tek”])

Upsert pattern:

```
INSERT INTO document_metadata (fireflies_id, title, started_at, ended_at, participants, storage_path, fireflies_summary, fireflies_actions, status)
VALUES (...)
ON CONFLICT (fireflies_id) DO UPDATE
SET title = EXCLUDED.title,
    started_at = EXCLUDED.started_at,
    ...
    last_processed_at = NOW();

Set status = 'raw_ingested' after this stage.
```

### 3. Stage 4–7: Segmenting, Chunking, Embedding → documents

#### Stage 4: Semantic segmentation (meeting → segments)

Now you run the segmenter: a single LLM call that turns the whole transcript into a structured JSON of segments.

Input prompt (conceptual):

You are analyzing a meeting transcript.
Split it into coherent segments based on topic shifts or agenda items.
For each segment, provide:
- title
- start_index (0-based index of the first character in the original transcript)
- end_index
- summary (5–10 bullet points)
- decisions (array of short decision statements)
- risks (array of short risk statements)
- tasks (array of short tasks with “assignee” and “due_date” if present)
Return strict JSON with:
{ "segments": [ ... ] }

Output schema example:

```
{
  "segments": [
    {
      "title": "Opening and project overview",
      "start_index": 0,
      "end_index": 3456,
      "summary": [
        "Reviewed ASRS project scope for Client X",
        "Aligned on overall schedule and target completion date"
      ],
      "decisions": [
        "Proceed with revised ASRS layout from Hy-Tek"
      ],
      "risks": [
        "Permitting delays could push schedule by 4-6 weeks"
      ],
      "tasks": [
        {
          "description": "Brandon to follow up with fire marshal about ASRS requirements",
          "assignee": "Brandon",
          "due_date": "2025-12-05"
        }
      ]
    },
    ...
  ]
}
```

Store this in a meeting_segments table OR as JSONB on document_metadata (but I recommend a proper table with one row per segment):
- id
- metadata_id (FK)
- segment_index
- title
- start_index, end_index
- summary (text)
- decisions (jsonb)
- risks (jsonb)
- tasks (jsonb)

Set status = 'segmented' for that document_metadata row when done.

#### Stage 5: Chunking within segments

For each segment:
	1.	Extract segment_text = transcript_text[start_index:end_index].
	2.	Split into 600–900 token chunks with 100–150 token overlap, respecting sentence boundaries.

Algorithm outline:

```
def chunk_segment(segment_text, max_tokens=800, overlap_tokens=120):
    sentences = split_into_sentences(segment_text)
    chunks = []
    current = []
    current_token_count = 0

    for sent in sentences:
        sent_tokens = estimate_tokens(sent)
        if current_token_count + sent_tokens > max_tokens and current:
            chunks.append(" ".join(current))
            # start new chunk with overlap
            overlap = trim_to_overlap(current, overlap_tokens)
            current = overlap + [sent]
            current_token_count = estimate_tokens(" ".join(current))
        else:
            current.append(sent)
            current_token_count += sent_tokens

    if current:
        chunks.append(" ".join(current))

    return chunks
```

For each chunk, you create a row to insert into documents later:
- id
- metadata_id
- segment_id
- chunk_index
- content (chunk text)
- doc_type = 'chunk'
- meeting_date = started_at
- participants
- project_id / client_id
- tags (maybe inherit from segment / document_metadata themes)

Set status = 'chunked' when all chunks are prepared (even before embeddings).

#### Stage 6: Embed segments + chunks + meeting summary

You want multiple embedding granularities:
	1.	Meeting-level:
- Text: “super summary” (you can generate a better summary now that you have segments).
- Save as documents row with doc_type = 'meeting_summary'.
	2.	Segment-level:
- Use segment summary text.
- Save as doc_type = 'segment_summary'.
	3.	Chunk-level:
- Use actual content (chunk text).
- Save as doc_type = 'chunk'.

You can batch all embedding requests per meeting to reduce overhead.

Pseudo:

texts_to_embed = []

# meeting summary

```
texts_to_embed.append({
  "key": ("meeting_summary", metadata_id),
  "text": meeting_super_summary_text
})
```

# segments
```
for segment in segments:
    texts_to_embed.append({
      "key": ("segment", segment.id),
      "text": "\n".join(segment.summary)
    })
```

# chunks
for chunk in chunks:

```
    texts_to_embed.append({
      "key": ("chunk", chunk.temp_id),
      "text": chunk.content
    })
```

embeddings = openai.embeddings.create(
    model="text-embedding-3-large",
    input=[t["text"] for t in texts_to_embed]
)

Then map back and bulk insert into documents:

documents columns (suggested):
- id
- metadata_id
- segment_id (nullable)
- doc_type (‘meeting_summary’ | ‘segment_summary’ | ‘chunk’)
- chunk_index (nullable)
- content
- embedding (vector)
- meeting_date
- participants
- project_id / client_id
- tags (text[])

Set status = 'embedded' afterward.



4. Stage 8: Structured extraction (decisions, risks, tasks, opportunities)

This is where the “strategist brain” unlocks.

Use the segment JSON you already generated (which includes decisions, risks, tasks per segment), plus optionally a second pass across the whole transcript for higher-level opportunities.

You can:
	1.	Aggregate segment-level decisions/risks/tasks into lists.
	2.	Run a second LLM pass to refine and deduplicate them, and to derive opportunities.

Example extraction prompt (high-level):

Given these segment-level decisions, risks, tasks, and the full meeting summary,
normalize them into:
- decisions (concise, specific, with owner if mentioned)
- risks (likelihood, impact, owner if mentioned)
- tasks (description, assignee, due date if mentioned, priority)
- opportunities (new ideas, improvements, or strategic options mentioned)
Return strict JSON lists for each type.

Output example:

{
  "decisions": [
    {
      "description": "Adopt Hy-Tek's revised ASRS sprinkler layout for Client X.",
      "owner": "Brandon",
      "project": "Client X ASRS",
      "effective_date": "2025-12-01"
    }
  ],
  "risks": [
    {
      "description": "Permitting delays may push ASRS install by 4-6 weeks.",
      "category": "Schedule",
      "likelihood": "high",
      "impact": "high",
      "owner": "Brandon"
    }
  ],
  "tasks": [
    {
      "description": "Confirm ASRS design checklist with fire marshal.",
      "assignee": "Brandon",
      "due_date": "2025-12-05",
      "priority": "high"
    }
  ],
  "opportunities": [
    {
      "description": "Standardize ASRS permitting checklist for all projects.",
      "type": "Process Improvement",
      "owner": "Operations"
    }
  ]
}

Now you insert into structured tables:
- decisions
- risks
- tasks
- opportunities

Each with:
- id
- metadata_id
- segment_id (optional; link back)
- description
- owner (nullable)
- project_id/client_id (nullable)
- domain fields (due_date, priority, likelihood, impact, type, etc.)
- source_chunk_id (optional: you can map each to a specific chunk for RAG provenance)
- embedding (vector for description)

Embedding: run another small batch embedding request over all description fields and store in each table.

Finally, set status = 'structured_extracted'.

### 5. Stage 9: Orchestration, Idempotency, and Backfill

To avoid chaos over 3+ years of data, you want a light orchestration model.

#### 9.1. Job table

fireflies_ingestion_jobs:
- id
- fireflies_id
- metadata_id (nullable until created)
- stage (‘pending’ | ‘raw_ingested’ | ‘segmented’ | ‘chunked’ | ‘embedded’ | ‘structured_extracted’ | ‘done’ | ‘error’)
- error_message
- last_attempt_at
- attempt_count

Each worker run:
	1.	Pull N jobs where stage != 'done' and stage != 'error' (or retry errors).
	2.	Run the next stage based on current stage.
	3.	Update stage and last_attempt_at.

Stages map 1:1 with our pipeline:
- pending → Stage 2–3 (fetch + metadata + storage) → raw_ingested
- raw_ingested → Stage 4 (segment) → segmented
- segmented → Stage 5 (chunk) → chunked
- chunked → Stage 6–7 (embeddings) → embedded
- embedded → Stage 8 (structured extraction) → structured_extracted
- structured_extracted → done

This lets you:
- Re-run part of pipeline if you improve segmenter/extractor.
- See where things are stuck.
- Avoid double-inserting because each stage updates existing rows (ON CONFLICT with fireflies_id or id).

#### 9.2. Idempotency rules
- document_metadata.fireflies_id = UNIQUE
- For meeting_segments: UNIQUE on (metadata_id, segment_index)
- For documents:
- For doc_type = 'chunk', unique on (metadata_id, segment_id, chunk_index)
- For doc_type = 'segment_summary', unique on (segment_id)
- For doc_type = 'meeting_summary', unique on (metadata_id, ‘meeting_summary’)
- For structured tables:
- You can use (metadata_id, description) as a soft uniqueness key to avoid duplicates on re-runs, or add a hash column.

Every insert uses ON CONFLICT DO UPDATE, so re-running just overwrites/improves.

9.3. Backfill vs real-time
- Backfill script:
- Iterate through all historical Fireflies meetings.
- For each, create a fireflies_ingestion_jobs row with stage='pending'.
- Let workers process them in batches (respect rate limits for Fireflies + OpenAI).
- Real-time:
- Webhook from Fireflies → create fireflies_ingestion_jobs row.
- Worker picks it up and runs full pipeline.

---

## SUPABASE TABLE SCHEMA'S

Here’s a concrete, implementation-ready schema set you can drop into Supabase (or vanilla Postgres) as your foundation.

I’ll give:
- Extensions
- document_metadata
- meeting_segments
- documents (embeddings)
- decisions, risks, tasks, opportunities
- fireflies_ingestion_jobs (to orchestrate the pipeline)

You can paste this whole thing into the SQL editor and tweak names/dimensions as needed.

### 0. Extensions

```
-- UUIDs for IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vector for embeddings (pgvector)
CREATE EXTENSION IF NOT EXISTS "vector";
```

### 1. document_metadata

One row per Fireflies meeting.

```
CREATE TABLE public.document_metadata (
  id               uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  fireflies_id     text NOT NULL UNIQUE,              -- external ID from Fireflies

  title            text,
  started_at       timestamptz NOT NULL,
  ended_at         timestamptz,
  duration_seconds integer GENERATED ALWAYS AS (
                     GREATEST(0, EXTRACT(epoch FROM (COALESCE(ended_at, started_at) - started_at)))::int
                   ) STORED,

  participants     jsonb NOT NULL DEFAULT '[]'::jsonb, -- [{name, email}, ...]
  storage_path     text NOT NULL,                      -- path in Supabase storage bucket

  fireflies_summary  text,
  fireflies_actions  jsonb NOT NULL DEFAULT '[]'::jsonb,

  -- Optional linkage to your own domain model
  project_id       bigint,                             -- FK to projects table, if you have one
  client_id        bigint,                             -- FK to clients table, if applicable

  themes           text[] NOT NULL DEFAULT '{}'::text[], -- tags like ['ASRS','permitting']

  status           text NOT NULL DEFAULT 'raw_ingested'
                   CHECK (status IN (
                     'pending',
                     'raw_ingested',
                     'segmented',
                     'chunked',
                     'embedded',
                     'structured_extracted',
                     'done',
                     'error'
                   )),

  last_processed_at timestamptz,
  error_message     text,

  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX document_metadata_started_at_idx
  ON public.document_metadata (started_at);

CREATE INDEX document_metadata_project_idx
  ON public.document_metadata (project_id);

CREATE INDEX document_metadata_client_idx
  ON public.document_metadata (client_id);

CREATE INDEX document_metadata_themes_gin_idx
  ON public.document_metadata
  USING gin (themes);

-- Optional trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION public.set_timestamp()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_document_metadata_timestamp
BEFORE UPDATE ON public.document_metadata
FOR EACH ROW
EXECUTE FUNCTION public.set_timestamp();
```

2. meeting_segments

Semantic segments inside a meeting.

```
CREATE TABLE public.meeting_segments (
  id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

  metadata_id   uuid NOT NULL
                REFERENCES public.document_metadata(id)
                ON DELETE CASCADE,

  segment_index integer NOT NULL,    -- 0,1,2,...
  title         text,
  start_index   integer NOT NULL,    -- char index in original transcript text
  end_index     integer NOT NULL,

  summary       text,                -- 5–10 bullet summary flattened as text
  decisions     jsonb NOT NULL DEFAULT '[]'::jsonb, -- raw extracted decisions (array)
  risks         jsonb NOT NULL DEFAULT '[]'::jsonb,
  tasks         jsonb NOT NULL DEFAULT '[]'::jsonb,

  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),

  UNIQUE (metadata_id, segment_index)
);

CREATE INDEX meeting_segments_metadata_idx
  ON public.meeting_segments (metadata_id);

CREATE TRIGGER set_meeting_segments_timestamp
BEFORE UPDATE ON public.meeting_segments
FOR EACH ROW
EXECUTE FUNCTION public.set_timestamp();
```

3. documents (embeddings + text chunks)

This is your general-purpose “vectorized artifacts” table.

```
-- Adjust dimension to your embedding model (e.g., 3072 or 1536)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type WHERE typname = 'embedding_vector'
  ) THEN
    CREATE TYPE embedding_vector AS RANGE (subtype = integer);
  END IF;
END$$;

-- We'll just use vector(3072) directly:
CREATE TABLE public.documents (
  id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

  metadata_id   uuid NOT NULL
                REFERENCES public.document_metadata(id)
                ON DELETE CASCADE,

  segment_id    uuid
                REFERENCES public.meeting_segments(id)
                ON DELETE SET NULL,

  doc_type      text NOT NULL
                CHECK (doc_type IN (
                  'meeting_summary',    -- 1 per meeting
                  'segment_summary',    -- 1 per segment
                  'chunk'               -- multiple per segment
                )),

  chunk_index   integer,                -- only for doc_type='chunk'
  content       text NOT NULL,          -- text used for embedding / retrieval

  embedding     vector(3072) NOT NULL,  -- adjust dimension here

  meeting_date  date,
  participants  jsonb NOT NULL DEFAULT '[]'::jsonb,
  project_id    bigint,
  client_id     bigint,
  tags          text[] NOT NULL DEFAULT '{}'::text[],

  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX documents_metadata_idx
  ON public.documents (metadata_id);

CREATE INDEX documents_segment_idx
  ON public.documents (segment_id);

CREATE INDEX documents_doc_type_idx
  ON public.documents (doc_type);

CREATE INDEX documents_project_idx
  ON public.documents (project_id);

CREATE INDEX documents_client_idx
  ON public.documents (client_id);

CREATE INDEX documents_tags_gin_idx
  ON public.documents
  USING gin (tags);

-- Vector index for fast similarity search
CREATE INDEX documents_embedding_ivfflat_idx
  ON public.documents
  USING ivfflat (embedding vector_l2_ops)
  WITH (lists = 100);

If you want stricter idempotency for chunks:

CREATE UNIQUE INDEX documents_chunk_unique_idx
  ON public.documents (metadata_id, segment_id, doc_type, COALESCE(chunk_index, -1));
```

4. decisions

Normalized decisions extracted from meetings.

```
CREATE TABLE public.decisions (
  id             uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

  metadata_id    uuid NOT NULL
                 REFERENCES public.document_metadata(id)
                 ON DELETE CASCADE,

  segment_id     uuid
                 REFERENCES public.meeting_segments(id)
                 ON DELETE SET NULL,

  source_chunk_id uuid
                 REFERENCES public.documents(id)
                 ON DELETE SET NULL,

  description    text NOT NULL,     -- canonical decision statement
  rationale      text,              -- optional explanation
  owner_name     text,
  owner_email    text,
  project_id     bigint,
  client_id      bigint,
  effective_date date,

  status         text NOT NULL DEFAULT 'decided'  -- extend: 'decided','reversed','pending'
                 CHECK (status IN ('decided','reversed','pending')),

  embedding      vector(3072),      -- embedding of description

  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),

  UNIQUE (metadata_id, description)
);

CREATE INDEX decisions_metadata_idx
  ON public.decisions (metadata_id);

CREATE INDEX decisions_project_idx
  ON public.decisions (project_id);

CREATE INDEX decisions_client_idx
  ON public.decisions (client_id);

CREATE INDEX decisions_effective_date_idx
  ON public.decisions (effective_date);

CREATE INDEX decisions_embedding_ivfflat_idx
  ON public.decisions
  USING ivfflat (embedding vector_l2_ops)
  WITH (lists = 50);

CREATE TRIGGER set_decisions_timestamp
BEFORE UPDATE ON public.decisions
FOR EACH ROW
EXECUTE FUNCTION public.set_timestamp();
```

5. risks

Normalized risks with basic risk fields.

```
CREATE TABLE public.risks (
  id             uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

  metadata_id    uuid NOT NULL
                 REFERENCES public.document_metadata(id)
                 ON DELETE CASCADE,

  segment_id     uuid
                 REFERENCES public.meeting_segments(id)
                 ON DELETE SET NULL,

  source_chunk_id uuid
                 REFERENCES public.documents(id)
                 ON DELETE SET NULL,

  description    text NOT NULL,
  category       text,                 -- e.g., 'Schedule','Cost','Quality','Client','Legal'
  likelihood     text,                 -- e.g., 'low','medium','high'
  impact         text,                 -- e.g., 'low','medium','high'
  owner_name     text,
  owner_email    text,
  project_id     bigint,
  client_id      bigint,
  status         text NOT NULL DEFAULT 'open'
                 CHECK (status IN ('open','mitigated','closed')),

  mitigation_plan text,

  embedding      vector(3072),

  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),

  UNIQUE (metadata_id, description)
);

CREATE INDEX risks_metadata_idx
  ON public.risks (metadata_id);

CREATE INDEX risks_project_idx
  ON public.risks (project_id);

CREATE INDEX risks_client_idx
  ON public.risks (client_id);

CREATE INDEX risks_status_idx
  ON public.risks (status);

CREATE INDEX risks_embedding_ivfflat_idx
  ON public.risks
  USING ivfflat (embedding vector_l2_ops)
  WITH (lists = 50);

CREATE TRIGGER set_risks_timestamp
BEFORE UPDATE ON public.risks
FOR EACH ROW
EXECUTE FUNCTION public.set_timestamp();
```

### 6. tasks (action items)

Action items from meetings that can also be synced to your PM system.

```
CREATE TABLE public.tasks (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

  metadata_id     uuid NOT NULL
                  REFERENCES public.document_metadata(id)
                  ON DELETE CASCADE,

  segment_id      uuid
                  REFERENCES public.meeting_segments(id)
                  ON DELETE SET NULL,

  source_chunk_id uuid
                  REFERENCES public.documents(id)
                  ON DELETE SET NULL,

  description     text NOT NULL,
  assignee_name   text,
  assignee_email  text,
  project_id      bigint,
  client_id       bigint,

  due_date        date,
  priority        text,                 -- e.g., 'low','medium','high','urgent'
  status          text NOT NULL DEFAULT 'open'
                  CHECK (status IN ('open','in_progress','blocked','done','cancelled')),

  source_system   text NOT NULL DEFAULT 'fireflies', -- later: 'manual','asana','clickup', etc.

  embedding       vector(3072),

  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),

  UNIQUE (metadata_id, description)
);

CREATE INDEX tasks_metadata_idx
  ON public.tasks (metadata_id);

CREATE INDEX tasks_project_idx
  ON public.tasks (project_id);

CREATE INDEX tasks_client_idx
  ON public.tasks (client_id);

CREATE INDEX tasks_due_date_idx
  ON public.tasks (due_date);

CREATE INDEX tasks_status_idx
  ON public.tasks (status);

CREATE INDEX tasks_embedding_ivfflat_idx
  ON public.tasks
  USING ivfflat (embedding vector_l2_ops)
  WITH (lists = 50);

CREATE TRIGGER set_tasks_timestamp
BEFORE UPDATE ON public.tasks
FOR EACH ROW
EXECUTE FUNCTION public.set_timestamp();
```

### 7. opportunities

Ideas / improvements / strategic opportunities.

```
CREATE TABLE public.opportunities (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

  metadata_id     uuid NOT NULL
                  REFERENCES public.document_metadata(id)
                  ON DELETE CASCADE,

  segment_id      uuid
                  REFERENCES public.meeting_segments(id)
                  ON DELETE SET NULL,

  source_chunk_id uuid
                  REFERENCES public.documents(id)
                  ON DELETE SET NULL,

  description     text NOT NULL,     -- canonical idea / opportunity
  type            text,              -- e.g., 'Process Improvement','Revenue','Cost Saving'
  owner_name      text,
  owner_email     text,
  project_id      bigint,
  client_id       bigint,

  status          text NOT NULL DEFAULT 'open'
                  CHECK (status IN ('open','in_review','approved','rejected','implemented')),

  embedding       vector(3072),

  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),

  UNIQUE (metadata_id, description)
);

CREATE INDEX opportunities_metadata_idx
  ON public.opportunities (metadata_id);

CREATE INDEX opportunities_project_idx
  ON public.opportunities (project_id);

CREATE INDEX opportunities_client_idx
  ON public.opportunities (client_id);

CREATE INDEX opportunities_status_idx
  ON public.opportunities (status);

CREATE INDEX opportunities_embedding_ivfflat_idx
  ON public.opportunities
  USING ivfflat (embedding vector_l2_ops)
  WITH (lists = 50);

CREATE TRIGGER set_opportunities_timestamp
BEFORE UPDATE ON public.opportunities
FOR EACH ROW
EXECUTE FUNCTION public.set_timestamp();
```

### 8. fireflies_ingestion_jobs (pipeline orchestration)

Tracks where each meeting is in the pipeline.

```
CREATE TABLE public.fireflies_ingestion_jobs (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

  fireflies_id    text NOT NULL UNIQUE,
  metadata_id     uuid
                  REFERENCES public.document_metadata(id)
                  ON DELETE SET NULL,

  stage           text NOT NULL DEFAULT 'pending'
                  CHECK (stage IN (
                    'pending',
                    'raw_ingested',
                    'segmented',
                    'chunked',
                    'embedded',
                    'structured_extracted',
                    'done',
                    'error'
                  )),

  attempt_count   integer NOT NULL DEFAULT 0,
  last_attempt_at timestamptz,
  error_message   text,

  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX fireflies_ingestion_jobs_stage_idx
  ON public.fireflies_ingestion_jobs (stage);

CREATE TRIGGER set_fireflies_ingestion_jobs_timestamp
BEFORE UPDATE ON public.fireflies_ingestion_jobs
FOR EACH ROW
EXECUTE FUNCTION public.set_timestamp();
```