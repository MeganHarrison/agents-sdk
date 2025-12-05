"""
RAG-based API endpoints for Alleato AI Chief of Staff
Handles chat interactions with retrieval from documents embeddings
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Query, Request
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

from alleato_agent_workflow.alleato_agent_workflow import (
    run_workflow,
    WorkflowInput,
    classification_agent,
    project,
    internal_knowledge_base,
    strategist,
)
from memory_store import MemoryStore

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Alleato RAG API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Context management
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

# Memory store for thread management
memory_store = MemoryStore[RagChatContext](
    create_thread=lambda thread_id: RagChatContext(context=create_initial_rag_context()),
    deserialize_thread=lambda data: RagChatContext(
        context=RagAgentContext(**data.get("context", {})),
        agents=data.get("agents", []),
        events=data.get("events", []),
        guardrails=data.get("guardrails", []),
    ),
)

# ChatKit server configuration
chatkit_server = ChatKitServer(
    store=memory_store,
    title="Alleato AI Chief of Staff",
)

# Handle agent streaming responses
async def handle_rag_agent_stream(
    thread_id: str,
    message: UserMessageItem,
    thread_metadata: ThreadMetadata | None = None,
) -> AsyncIterator[ThreadStreamEvent]:
    """Handle streaming responses from RAG agents"""

    # Get or create thread context
    try:
        chat_context = memory_store.get_thread(thread_id)
    except NotFoundError:
        chat_context = RagChatContext(context=create_initial_rag_context())
        memory_store.set_thread(thread_id, chat_context)

    # Extract user message
    user_input = ""
    if message.content:
        for content_item in message.content:
            if hasattr(content_item, 'text'):
                user_input = content_item.text
                break

    # Log the agent event
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

        # Parse result based on type
        if isinstance(result, dict):
            # Handle guardrail failures
            if "pii" in result or "jailbreak" in result:
                chat_context.guardrails.append({
                    "type": "guardrail_triggered",
                    "timestamp": datetime.now().isoformat(),
                    "details": result,
                })
                response_text = "I cannot process this request due to policy violations."
            else:
                response_text = result.get("safe_text", "I encountered an issue processing your request.")
        elif isinstance(result, str):
            response_text = result
        else:
            response_text = str(result)

        # Update context based on classification
        if "classification" in str(result):
            if "project" in str(result).lower():
                chat_context.context.current_agent = "project"
                chat_context.context.query_type = "project"
            elif "policy" in str(result).lower():
                chat_context.context.current_agent = "internal_knowledge"
                chat_context.context.query_type = "policy"
            elif "strategic" in str(result).lower():
                chat_context.context.current_agent = "strategist"
                chat_context.context.query_type = "strategic"

        # Add agent to list if not present
        if chat_context.context.current_agent not in chat_context.agents:
            chat_context.agents.append(chat_context.context.current_agent)

        # Create assistant response
        assistant_message = AssistantMessageItem(
            item_id=str(uuid4()),
            content=[
                AssistantMessageContent(
                    type="text",
                    text=response_text,
                )
            ],
            created_at=int(time.time() * 1000),
        )

        # Yield the assistant message
        yield assistant_message

        # Update memory store
        memory_store.set_thread(thread_id, chat_context)

        # Send done event
        yield ThreadItemDoneEvent(
            type="thread.item.done",
            item_id=assistant_message.item_id,
        )

    except Exception as e:
        logger.error(f"Error in RAG agent stream: {e}")
        error_message = AssistantMessageItem(
            item_id=str(uuid4()),
            content=[
                AssistantMessageContent(
                    type="text",
                    text=f"I encountered an error processing your request: {str(e)}",
                )
            ],
            created_at=int(time.time() * 1000),
        )
        yield error_message
        yield ThreadItemDoneEvent(
            type="thread.item.done",
            item_id=error_message.item_id,
        )

# Register the handler with ChatKit server
chatkit_server.handle_stream_event = handle_rag_agent_stream

# API endpoints
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rag-api"}

@app.post("/rag-chatkit")
async def rag_chatkit_endpoint(request: Request):
    """Main RAG ChatKit endpoint"""
    return await chatkit_server.handle_request(request)

@app.get("/rag-chatkit/state")
async def get_rag_state(thread_id: str = Query(...)):
    """Get current RAG conversation state"""
    try:
        chat_context = memory_store.get_thread(thread_id)
        return {
            "thread_id": thread_id,
            "current_agent": chat_context.context.current_agent,
            "agents": chat_context.agents,
            "events": chat_context.events,
            "guardrails": chat_context.guardrails,
            "context": chat_context.context.to_dict(),
        }
    except NotFoundError:
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
    thread_id = str(uuid4())
    context = create_initial_rag_context()
    context.thread_id = thread_id

    chat_context = RagChatContext(context=context)
    chat_context.agents = ["classification"]

    memory_store.set_thread(thread_id, chat_context)

    return {
        "thread_id": thread_id,
        "current_agent": "classification",
        "agents": chat_context.agents,
        "events": [],
        "guardrails": [],
        "context": context.to_dict(),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)