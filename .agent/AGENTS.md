# AGENTS

## What the Agent Is Designed to Do

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

## Core Principles

1. **Plan before you build**
   - Complex work must start from an explicit plan (ExecPlan) rather than ad-hoc coding.
2. **Automated validation by default**
   - Every meaningful change (feature, refactor, bug fix) must be validated via **Playwright**.
3. **Single source of truth**
   - Keep documentation and this `AGENTS.md` in sync with reality.

---

# ExecPlans
 When writing complex features or significant refactors, use an ExecPlan (as described in .agent/PLANS.md) from design to implementation.

---

## Validation & QA (Playwright Required)

> **Very important:** All tasks must be validated using **Playwright**.

### Requirements

- **Every meaningful change** must have corresponding Playwright coverage:
  - New features → new Playwright specs verifying happy path + key edge cases.
  - Bug fixes → reproducing tests that fail before the fix and pass after.
  - Refactors → tests updated or extended to ensure no regressions.
- **No “done” without Playwright**:
  - A task is not considered complete until:
    - Relevant Playwright tests exist, and
    - `pnpm playwright test` (or equivalent command) passes.

## Documentation Discipline

> Keep documentation up to date.  
> Update planning and tasks documents as things are completed.

### Rules

- After completing a task:
  - Mark the task as **DONE**.
  - Add a brief note of what changed and where tests live.
  - Link to any associated ExecPlan or PR.
- When abandoning or changing direction on a plan:
  - Update or close the old ExecPlan; do not leave stale plans hanging.
- When changing how agents or tools behave:
  - Update this `AGENTS.md` file.