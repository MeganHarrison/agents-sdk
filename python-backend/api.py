from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

# Load environment variables from root .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from agents import (
    Handoff,
    HandoffOutputItem,
    InputGuardrailTripwireTriggered,
    ItemHelpers,
    MessageOutputItem,
    Runner,
    ToolCallItem,
    ToolCallOutputItem,
)
from chatkit.agents import stream_agent_response
from chatkit.server import ChatKitServer, StreamingResult
from chatkit.types import (
    Action,
    AssistantMessageContent,
    AssistantMessageItem,
    ThreadItemDoneEvent,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
)
from chatkit.store import NotFoundError

from main import (
    AirlineAgentChatContext,
    AirlineAgentContext,
    cancellation_agent,
    create_initial_context,
    faq_agent,
    flight_status_agent,
    seat_booking_agent,
    triage_agent,
)
from memory_store import MemoryStore
from supabase_helpers import SupabaseRagStore
from ingestion.fireflies_pipeline import FirefliesIngestionPipeline

# Import RAG workflow components
try:
    from alleato_agent_workflow.alleato_agent_workflow import (
        run_workflow,
        WorkflowInput,
        classification_agent as rag_classification_agent,
        project as rag_project_agent,
        internal_knowledge_base as rag_knowledge_agent,
        strategist as rag_strategist_agent,
    )
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("Warning: RAG workflow not available. Continuing with airline demo only.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration (adjust as needed for deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentEvent(BaseModel):
    id: str
    type: str
    agent: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None


class GuardrailCheck(BaseModel):
    id: str
    name: str
    input: str
    reasoning: str
    passed: bool
    timestamp: float


class ChatRequest(BaseModel):
    message: str
    project_id: Optional[int] = None
    limit: int = 5


class IngestRequest(BaseModel):
    path: str
    project_id: Optional[int] = None
    dry_run: bool = True


def _get_agent_by_name(name: str):
    """Return the agent object by name."""
    agents = {
        triage_agent.name: triage_agent,
        faq_agent.name: faq_agent,
        seat_booking_agent.name: seat_booking_agent,
        flight_status_agent.name: flight_status_agent,
        cancellation_agent.name: cancellation_agent,
    }
    return agents.get(name, triage_agent)


def _get_guardrail_name(g) -> str:
    """Extract a friendly guardrail name."""
    name_attr = getattr(g, "name", None)
    if isinstance(name_attr, str) and name_attr:
        return name_attr
    guard_fn = getattr(g, "guardrail_function", None)
    if guard_fn is not None and hasattr(guard_fn, "__name__"):
        return guard_fn.__name__.replace("_", " ").title()
    fn_name = getattr(g, "__name__", None)
    if isinstance(fn_name, str) and fn_name:
        return fn_name.replace("_", " ").title()
    return str(g)


def _build_agents_list() -> List[Dict[str, Any]]:
    """Build a list of all available agents and their metadata."""

    def make_agent_dict(agent):
        return {
            "name": agent.name,
            "description": getattr(agent, "handoff_description", ""),
            "handoffs": [getattr(h, "agent_name", getattr(h, "name", "")) for h in getattr(agent, "handoffs", [])],
            "tools": [getattr(t, "name", getattr(t, "__name__", "")) for t in getattr(agent, "tools", [])],
            "input_guardrails": [_get_guardrail_name(g) for g in getattr(agent, "input_guardrails", [])],
        }

    return [
        make_agent_dict(triage_agent),
        make_agent_dict(faq_agent),
        make_agent_dict(seat_booking_agent),
        make_agent_dict(flight_status_agent),
        make_agent_dict(cancellation_agent),
    ]


def _user_message_to_text(message: UserMessageItem) -> str:
    parts: List[str] = []
    for part in message.content:
        text = getattr(part, "text", "")
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts)


def _parse_tool_args(raw_args: Any) -> Any:
    if isinstance(raw_args, str):
        try:
            import json

            return json.loads(raw_args)
        except Exception:
            return raw_args
    return raw_args


@dataclass
class ConversationState:
    input_items: List[Any] = field(default_factory=list)
    context: AirlineAgentContext = field(default_factory=create_initial_context)
    current_agent_name: str = triage_agent.name
    events: List[AgentEvent] = field(default_factory=list)
    guardrails: List[GuardrailCheck] = field(default_factory=list)


class AirlineServer(ChatKitServer[dict[str, Any]]):
    def __init__(self) -> None:
        self.store = MemoryStore()
        super().__init__(self.store)
        self._state: Dict[str, ConversationState] = {}

    def _state_for_thread(self, thread_id: str) -> ConversationState:
        if thread_id not in self._state:
            self._state[thread_id] = ConversationState()
        return self._state[thread_id]

    async def _ensure_thread(
        self, thread_id: Optional[str], context: dict[str, Any]
    ) -> ThreadMetadata:
        if thread_id:
            try:
                return await self.store.load_thread(thread_id, context)
            except NotFoundError:
                pass
        new_thread = ThreadMetadata(id=self.store.generate_thread_id(context), created_at=datetime.now())
        await self.store.save_thread(new_thread, context)
        self._state_for_thread(new_thread.id)
        return new_thread

    def _record_guardrails(
        self,
        agent_name: str,
        input_text: str,
        guardrail_results: List[Any],
    ) -> List[GuardrailCheck]:
        checks: List[GuardrailCheck] = []
        timestamp = time.time() * 1000
        agent = _get_agent_by_name(agent_name)
        for guardrail in getattr(agent, "input_guardrails", []):
            result = next((r for r in guardrail_results if r.guardrail == guardrail), None)
            reasoning = ""
            passed = True
            if result:
                info = getattr(result.output, "output_info", None)
                reasoning = getattr(info, "reasoning", "") or reasoning
                passed = not result.output.tripwire_triggered
            checks.append(
                GuardrailCheck(
                    id=uuid4().hex,
                    name=_get_guardrail_name(guardrail),
                    input=input_text,
                    reasoning=reasoning,
                    passed=passed,
                    timestamp=timestamp,
                )
            )
        return checks

    def _record_events(
        self,
        run_items: List[Any],
        current_agent_name: str,
    ) -> (List[AgentEvent], str):
        events: List[AgentEvent] = []
        active_agent = current_agent_name
        now_ms = time.time() * 1000

        for item in run_items:
            if isinstance(item, MessageOutputItem):
                text = ItemHelpers.text_message_output(item)
                events.append(
                    AgentEvent(
                        id=uuid4().hex,
                        type="message",
                        agent=item.agent.name,
                        content=text,
                        timestamp=now_ms,
                    )
                )
            elif isinstance(item, HandoffOutputItem):
                events.append(
                    AgentEvent(
                        id=uuid4().hex,
                        type="handoff",
                        agent=item.source_agent.name,
                        content=f"{item.source_agent.name} -> {item.target_agent.name}",
                        metadata={"source_agent": item.source_agent.name, "target_agent": item.target_agent.name},
                        timestamp=now_ms,
                    )
                )

                from_agent = item.source_agent
                to_agent = item.target_agent
                ho = next(
                    (
                        h
                        for h in getattr(from_agent, "handoffs", [])
                        if isinstance(h, Handoff) and getattr(h, "agent_name", None) == to_agent.name
                    ),
                    None,
                )
                if ho:
                    fn = ho.on_invoke_handoff
                    fv = fn.__code__.co_freevars
                    cl = fn.__closure__ or []
                    if "on_handoff" in fv:
                        idx = fv.index("on_handoff")
                        if idx < len(cl) and cl[idx].cell_contents:
                            cb = cl[idx].cell_contents
                            cb_name = getattr(cb, "__name__", repr(cb))
                            events.append(
                                AgentEvent(
                                    id=uuid4().hex,
                                    type="tool_call",
                                    agent=to_agent.name,
                                    content=cb_name,
                                    timestamp=now_ms,
                                )
                            )

                active_agent = to_agent.name
            elif isinstance(item, ToolCallItem):
                tool_name = getattr(item.raw_item, "name", None)
                raw_args = getattr(item.raw_item, "arguments", None)
                events.append(
                    AgentEvent(
                        id=uuid4().hex,
                        type="tool_call",
                        agent=item.agent.name,
                        content=tool_name or "",
                        metadata={"tool_args": _parse_tool_args(raw_args)},
                        timestamp=now_ms,
                    )
                )
            elif isinstance(item, ToolCallOutputItem):
                events.append(
                    AgentEvent(
                        id=uuid4().hex,
                        type="tool_output",
                        agent=item.agent.name,
                        content=str(item.output),
                        metadata={"tool_result": item.output},
                        timestamp=now_ms,
                    )
                )

        return events, active_agent

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        state = self._state_for_thread(thread.id)
        user_text = ""
        if input_user_message is not None:
            user_text = _user_message_to_text(input_user_message)
            state.input_items.append({"content": user_text, "role": "user"})

        previous_context = state.context.model_dump()
        chat_context = AirlineAgentChatContext(
            thread=thread,
            store=self.store,
            request_context=context,
            state=state.context,
        )

        try:
            result = Runner.run_streamed(
                _get_agent_by_name(state.current_agent_name),
                state.input_items,
                context=chat_context,
            )
            async for event in stream_agent_response(chat_context, result):
                yield event
        except InputGuardrailTripwireTriggered as exc:
            failed_guardrail = exc.guardrail_result.guardrail
            gr_output = exc.guardrail_result.output.output_info
            reasoning = getattr(gr_output, "reasoning", "")
            timestamp = time.time() * 1000
            checks: List[GuardrailCheck] = []
            for guardrail in _get_agent_by_name(state.current_agent_name).input_guardrails:
                checks.append(
                    GuardrailCheck(
                        id=uuid4().hex,
                        name=_get_guardrail_name(guardrail),
                        input=user_text,
                        reasoning=reasoning if guardrail == failed_guardrail else "",
                        passed=guardrail != failed_guardrail,
                        timestamp=timestamp,
                    )
                )
            state.guardrails = checks
            refusal = "Sorry, I can only answer questions related to airline travel."
            state.input_items.append({"role": "assistant", "content": refusal})
            yield ThreadItemDoneEvent(
                item=AssistantMessageItem(
                    id=self.store.generate_item_id("message", thread, context),
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    content=[AssistantMessageContent(text=refusal)],
                )
            )
            return

        state.input_items = result.to_input_list()
        new_events, active_agent = self._record_events(result.new_items, state.current_agent_name)
        state.events.extend(new_events)
        final_agent_name = active_agent
        try:
            final_agent_name = result.last_agent.name
        except Exception:
            pass
        state.current_agent_name = final_agent_name
        state.guardrails = self._record_guardrails(
            agent_name=state.current_agent_name,
            input_text=user_text,
            guardrail_results=result.input_guardrail_results,
        )

        new_context = state.context.model_dump()
        changes = {k: new_context[k] for k in new_context if previous_context.get(k) != new_context[k]}
        if changes:
            state.events.append(
                AgentEvent(
                    id=uuid4().hex,
                    type="context_update",
                    agent=state.current_agent_name,
                    content="",
                    metadata={"changes": changes},
                    timestamp=time.time() * 1000,
                )
            )

    async def action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        # No client-handled actions in this demo.
        if False:
            yield

    async def snapshot(self, thread_id: Optional[str], context: dict[str, Any]) -> Dict[str, Any]:
        thread = await self._ensure_thread(thread_id, context)
        state = self._state_for_thread(thread.id)
        return {
            "thread_id": thread.id,
            "current_agent": state.current_agent_name,
            "context": state.context.model_dump(),
            "agents": _build_agents_list(),
            "events": [e.model_dump() for e in state.events],
            "guardrails": [g.model_dump() for g in state.guardrails],
        }


server = AirlineServer()


def get_server() -> AirlineServer:
    return server


def get_rag_store() -> SupabaseRagStore:
    return SupabaseRagStore()


def get_ingestion_pipeline(
    store: SupabaseRagStore = Depends(get_rag_store),
) -> FirefliesIngestionPipeline:
    return FirefliesIngestionPipeline(store)


@app.post("/chatkit")
async def chatkit_endpoint(
    request: Request, server: AirlineServer = Depends(get_server)
) -> Response:
    payload = await request.body()
    result = await server.process(payload, {"request": request})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return Response(content=result)


@app.get("/chatkit/state")
async def chatkit_state(
    thread_id: str = Query(..., description="ChatKit thread identifier"),
    server: AirlineServer = Depends(get_server),
) -> Dict[str, Any]:
    return await server.snapshot(thread_id, {"request": None})


@app.get("/chatkit/bootstrap")
async def chatkit_bootstrap(
    server: AirlineServer = Depends(get_server),
) -> Dict[str, Any]:
    return await server.snapshot(None, {"request": None})


@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}


# ===== RAG ENDPOINTS =====
# These endpoints provide RAG-based chat functionality using Alleato agents

# RAG Context management
@dataclass
class RagAgentContext:
    """Context for RAG agent operations"""
    retrieved_chunks: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    query_type: Optional[str] = None
    current_agent: str = "classification"
    thread_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict:
        return {
            "retrieved_chunks": self.retrieved_chunks,
            "sources": self.sources,
            "confidence_score": self.confidence_score,
            "query_type": self.query_type,
            "current_agent": self.current_agent,
            "thread_id": self.thread_id,
        }

@dataclass
class RagChatContext:
    """Complete chat context including agents and events"""
    context: RagAgentContext
    agents: List[str] = field(default_factory=list)
    events: List[dict] = field(default_factory=list)
    guardrails: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "context": self.context.to_dict(),
            "agents": self.agents,
            "events": self.events,
            "guardrails": self.guardrails,
        }

def create_initial_rag_context() -> RagAgentContext:
    """Create initial RAG context"""
    return RagAgentContext()

# Memory store for RAG threads - simple dictionary storage
rag_memory_store: Dict[str, RagChatContext] = {}


@app.post("/rag-chatkit")
async def rag_chatkit_endpoint(request: Request):
    """Main RAG ChatKit endpoint"""
    if not RAG_AVAILABLE:
        return Response(
            content='{"error": "RAG workflow not available"}',
            status_code=503,
            media_type="application/json"
        )

    payload = await request.body()
    payload_json = json.loads(payload)

    thread_id = payload_json.get("thread_id") or str(uuid4())
    messages = payload_json.get("messages", [])

    # Get or create thread context
    if thread_id not in rag_memory_store:
        chat_context = RagChatContext(context=create_initial_rag_context())
        rag_memory_store[thread_id] = chat_context
    else:
        chat_context = rag_memory_store[thread_id]

    # Extract last user message
    user_input = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", [])
            for item in content:
                if item.get("type") == "text":
                    user_input = item.get("text", "")
                    break
            if user_input:
                break

    # Log the event
    event = {
        "type": "message",
        "timestamp": datetime.now().isoformat(),
        "agent": chat_context.context.current_agent,
        "message": user_input,
    }
    chat_context.events.append(event)

    try:
        # Run the workflow
        workflow_input = WorkflowInput(input_as_text=user_input)
        result = await run_workflow(workflow_input)

        # Parse result
        if isinstance(result, dict):
            if "pii" in result or "jailbreak" in result:
                chat_context.guardrails.append({
                    "type": "guardrail_triggered",
                    "timestamp": datetime.now().isoformat(),
                    "details": result,
                })
                response_text = "I cannot process this request due to policy violations."
            else:
                response_text = result.get("safe_text", str(result))
        else:
            response_text = str(result)

        # Update context
        if "project" in response_text.lower():
            chat_context.context.current_agent = "project"
        elif "policy" in response_text.lower():
            chat_context.context.current_agent = "internal_knowledge"
        elif "strategic" in response_text.lower():
            chat_context.context.current_agent = "strategist"

        # Update memory
        rag_memory_store[thread_id] = chat_context

        # Return response
        return Response(
            content=json.dumps({
                "messages": [
                    {
                        "role": "assistant",
                        "content": [{"type": "text", "text": response_text}]
                    }
                ],
                "thread_id": thread_id
            }),
            media_type="application/json"
        )

    except Exception as e:
        logger.error(f"Error in RAG workflow: {e}")
        return Response(
            content=json.dumps({
                "error": f"Error processing request: {str(e)}"
            }),
            status_code=500,
            media_type="application/json"
        )


@app.get("/rag-chatkit/state")
async def get_rag_state(thread_id: str = Query(...)):
    """Get current RAG conversation state"""
    if not RAG_AVAILABLE:
        return {"error": "RAG workflow not available"}

    if thread_id in rag_memory_store:
        chat_context = rag_memory_store[thread_id]
        return {
            "thread_id": thread_id,
            "current_agent": chat_context.context.current_agent,
            "agents": chat_context.agents,
            "events": chat_context.events,
            "guardrails": chat_context.guardrails,
            "context": chat_context.context.to_dict(),
        }
    else:
        return {
            "thread_id": thread_id,
            "current_agent": None,
            "agents": [],
            "events": [],
            "guardrails": [],
            "context": {},
        }


@app.get("/rag-chatkit/bootstrap")
async def rag_bootstrap():
    """Bootstrap a new RAG conversation"""
    if not RAG_AVAILABLE:
        return {"error": "RAG workflow not available"}

    thread_id = str(uuid4())
    context = create_initial_rag_context()
    context.thread_id = thread_id

    chat_context = RagChatContext(context=context)
    chat_context.agents = ["classification"]

    rag_memory_store[thread_id] = chat_context

    return {
        "thread_id": thread_id,
        "current_agent": "classification",
        "agents": chat_context.agents,
        "events": [],
        "guardrails": [],
        "context": context.to_dict(),
    }


def _select_keyword(message: str) -> Optional[str]:
    words = re.findall(r"[A-Za-z]+", message.lower())
    for word in words:
        if len(word) >= 4:
            return word
    return None


def _build_chat_reply(
    message: str,
    store: SupabaseRagStore,
    project_id: Optional[int],
    limit: int = 5,
) -> Dict[str, Any]:
    keyword = _select_keyword(message)
    chunks = store.search_chunks_by_keyword(keyword, project_id=project_id, limit=limit)
    if not chunks:
        chunks = store.fetch_recent_chunks(project_id=project_id, limit=limit)

    tasks = store.list_tasks(project_id=project_id, status="open", limit=limit)
    insights = store.list_insights(project_id=project_id, limit=limit)
    project = store.get_project(project_id) if project_id is not None else None

    sources = [
        {
            "document_id": chunk.get("document_id"),
            "chunk_index": chunk.get("chunk_index") or (chunk.get("metadata") or {}).get("chunk_index"),
            "snippet": (chunk.get("text") or "")[:280],
            "metadata": chunk.get("metadata") or {},
        }
        for chunk in chunks
    ]

    reply_lines: List[str] = []
    if project:
        reply_lines.append(
            f"Project {project.get('name', project_id)} has {project.get('meeting_count', 0)} documented meetings and {project.get('open_tasks', 0)} open AI tasks."
        )
    if tasks:
        reply_lines.append(
            "Top open tasks: " + "; ".join(task.get("title", "Task") for task in tasks[:3])
        )
    if insights:
        reply_lines.append(
            "Recent insights: " + "; ".join(insight.get("summary", "")[:80] for insight in insights[:3])
        )
    if sources:
        reply_lines.append(
            f"Retrieved {len(sources)} transcript snippets based on the keyword '{keyword or 'recent'}'."
        )
    if not reply_lines:
        reply_lines.append(
            "No relevant transcripts or tasks were found yet. Try ingesting more Fireflies meetings or widening your query."
        )

    return {
        "reply": "\n".join(reply_lines),
        "sources": sources,
        "tasks": tasks,
        "insights": insights,
    }


# === Alleato REST API ===


@app.get("/api/projects")
def list_projects_api(store: SupabaseRagStore = Depends(get_rag_store)) -> Dict[str, Any]:
    return {"projects": store.list_projects()}


@app.get("/api/projects/{project_id}")
def project_detail_api(project_id: int, store: SupabaseRagStore = Depends(get_rag_store)) -> Dict[str, Any]:
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = store.list_tasks(project_id=project_id, status="open", limit=50)
    insights = store.list_insights(project_id=project_id, limit=20)
    return {"project": project, "tasks": tasks, "insights": insights}


@app.post("/api/chat")
def rag_chat_api(payload: ChatRequest, store: SupabaseRagStore = Depends(get_rag_store)) -> Dict[str, Any]:
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    return _build_chat_reply(payload.message, store=store, project_id=payload.project_id, limit=payload.limit)


@app.post("/api/ingest/fireflies")
def ingest_fireflies_endpoint(
    payload: IngestRequest,
    pipeline: FirefliesIngestionPipeline = Depends(get_ingestion_pipeline),
) -> Dict[str, Any]:
    result = pipeline.ingest_file(payload.path, project_id=payload.project_id, dry_run=payload.dry_run)
    return {"result": result.__dict__}
