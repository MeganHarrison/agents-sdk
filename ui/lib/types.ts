export interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  agent?: string
  timestamp: Date
}

export interface Agent {
  name: string
  description: string
  handoffs: string[]
  tools: string[]
  /** List of input guardrail identifiers for this agent */
  input_guardrails: string[]
}

export type EventType = "message" | "handoff" | "tool_call" | "tool_output" | "context_update"

export interface AgentEvent {
  id: string
  type: EventType
  agent: string
  content: string
  timestamp: Date
  metadata?: {
    source_agent?: string
    target_agent?: string
    tool_name?: string
    tool_args?: Record<string, any>
    tool_result?: any
    context_key?: string
    context_value?: any
    changes?: Record<string, any>
  }
}

export interface GuardrailCheck {
  id: string
  name: string
  input: string
  reasoning: string
  passed: boolean
  timestamp: Date
}

export interface ProjectSummary {
  project_id: number
  name: string
  meeting_count: number
  open_tasks: number
  last_meeting_at?: string | null
  last_task_update?: string | null
  phase?: string | null
}

export interface TaskItem {
  id: string
  title: string
  description?: string | null
  status: string
  due_date?: string | null
  project_id?: number | null
  source_document_id?: string | null
}

export interface InsightItem {
  id?: string
  project_id: number
  summary: string
  detail?: Record<string, any>
  severity?: string | null
  captured_at?: string | null
}

export interface ChatSourceSnippet {
  document_id: string
  chunk_index: number
  snippet: string
  metadata?: Record<string, any>
}

export interface ChatAnswer {
  reply: string
  sources: ChatSourceSnippet[]
  tasks: TaskItem[]
  insights: InsightItem[]
}
