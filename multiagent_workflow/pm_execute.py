import os
import asyncio
from dotenv import load_dotenv

from agents import Agent, Runner, WebSearchTool, ModelSettings, set_default_openai_api
from agents.mcp import MCPServerStdio
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from openai.types.shared import Reasoning

# This script is intended to be run from the multiagent_workflow folder.
# Directory layout:
#   root/
#     .agent/PLANS.md
#     multiagent_workflow/
#       initiate_project.md
#       pm_planning.py
#       pm_execute.py
#       (generated planning artifacts)

# Load API key from .env
load_dotenv(override=True)
set_default_openai_api(os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EXEC_PLAN_PATH = os.path.join(BASE_DIR, "EXEC_PLAN.md")
REQUIREMENTS_PATH = os.path.join(BASE_DIR, "REQUIREMENTS.md")
TEST_PATH = os.path.join(BASE_DIR, "TEST.md")
AGENT_TASKS_PATH = os.path.join(BASE_DIR, "AGENT_TASKS.md")


async def main() -> None:
    # Make sure planning artifacts exist before we start execution
    required_files = [
        EXEC_PLAN_PATH,
        REQUIREMENTS_PATH,
        TEST_PATH,
        AGENT_TASKS_PATH,
    ]
    missing = [p for p in required_files if not os.path.exists(p)]
    if missing:
        msg = "Missing required planning artifacts:\n" + "\n".join(f"- {p}" for p in missing)
        msg += "\n\nRun pm_planning.py first to generate EXEC_PLAN.md, REQUIREMENTS.md, TEST.md, and AGENT_TASKS.md."
        raise RuntimeError(msg)

    async with MCPServerStdio(
        name="Codex CLI",
        params={"command": "npx", "args": ["-y", "codex", "mcp"]},
        client_session_timeout_seconds=360000,
    ) as codex_mcp_server:

        # ---------------------------
        # Downstream agents
        # ---------------------------

        designer_agent = Agent(
            name="Designer",
            instructions=(
                f"""{RECOMMENDED_PROMPT_PREFIX}"""
                "You are the Designer.\n"
                "Your primary sources of truth are EXEC_PLAN.md, AGENT_TASKS.md, and REQUIREMENTS.md in the current workspace.\n"
                "Do not assume anything that is not written there.\n\n"
                "You may use the internet for additional guidance or research.\n\n"
                "Deliverables (write to /design):\n"
                "- design_spec.md – a single page describing the UI/UX layout, main screens, and key visual notes as requested in AGENT_TASKS.md.\n"
                "- wireframe.md – a simple text or ASCII wireframe if specified.\n\n"
                "Keep the output short and implementation-friendly.\n"
                "When complete, handoff to the Project Manager with transfer_to_project_manager.\n"
                "When creating files, call Codex MCP with {\"approval-policy\":\"never\",\"sandbox\":\"workspace-write\"}.\n"
            ),
            model="gpt-5",
            tools=[WebSearchTool()],
            mcp_servers=[codex_mcp_server],
            handoffs=[],
        )

        frontend_developer_agent = Agent(
            name="Frontend Developer",
            instructions=(
                f"""{RECOMMENDED_PROMPT_PREFIX}"""
                "You are the Frontend Developer.\n"
                "Read EXEC_PLAN.md, AGENT_TASKS.md, and /design/design_spec.md. Implement exactly what is described there.\n\n"
                "Deliverables (write to /frontend):\n"
                "- index.html – main page structure\n"
                "- styles.css or inline styles if specified\n"
                "- main.js or game.js if specified\n\n"
                "Follow the Designer’s DOM structure and any integration points given by the Project Manager.\n"
                "Do not add features or branding beyond the provided documents.\n\n"
                "When complete, handoff to the Project Manager with transfer_to_project_manager_agent.\n"
                "When creating files, call Codex MCP with {\"approval-policy\":\"never\",\"sandbox\":\"workspace-write\"}.\n"
            ),
            model="gpt-5",
            mcp_servers=[codex_mcp_server],
            handoffs=[],
        )

        backend_developer_agent = Agent(
            name="Backend Developer",
            instructions=(
                f"""{RECOMMENDED_PROMPT_PREFIX}"""
                "You are the Backend Developer.\n"
                "Read EXEC_PLAN.md, AGENT_TASKS.md, and REQUIREMENTS.md. Implement the backend endpoints described there.\n\n"
                "Deliverables (write to /backend):\n"
                "- package.json – include a start script if requested\n"
                "- server.js – implement the API endpoints and logic exactly as specified\n\n"
                "Keep the code as simple and readable as possible. No external database.\n\n"
                "When complete, handoff to the Project Manager with transfer_to_project_manager_agent.\n"
                "When creating files, call Codex MCP with {\"approval-policy\":\"never\",\"sandbox\":\"workspace-write\"}.\n"
            ),
            model="gpt-5",
            mcp_servers=[codex_mcp_server],
            handoffs=[],
        )

        tester_agent = Agent(
            name="Tester",
            instructions=(
                f"""{RECOMMENDED_PROMPT_PREFIX}"""
                "You are the Tester.\n"
                "Read EXEC_PLAN.md, AGENT_TASKS.md, and TEST.md. Verify that the outputs of the other roles meet the acceptance criteria.\n\n"
                "Deliverables (write to /tests):\n"
                "- TEST_PLAN.md – bullet list of manual checks or automated steps as requested\n"
                "- test.sh or a simple automated script if specified\n\n"
                "Keep it minimal and easy to run.\n\n"
                "When complete, handoff to the Project Manager with transfer_to_project_manager.\n"
                "When creating files, call Codex MCP with {\"approval-policy\":\"never\",\"sandbox\":\"workspace-write\"}.\n"
            ),
            model="gpt-5",
            mcp_servers=[codex_mcp_server],
            handoffs=[],
        )

        # ---------------------------
        # Project Manager (execution/gating)
        # ---------------------------

        project_manager_agent = Agent(
            name="Project Manager",
            instructions=(
                f"""{RECOMMENDED_PROMPT_PREFIX}"""
                f"""
You are the Project Manager responsible for EXECUTION and GATING.

Assume the following files ALREADY EXIST in the current workspace (multiagent_workflow):
- {EXEC_PLAN_PATH}
- {REQUIREMENTS_PATH}
- {TEST_PATH}
- {AGENT_TASKS_PATH}

Do NOT recreate or overwrite these planning documents, except to update EXEC_PLAN.md's
Progress, Surprises & Discoveries, Decision Log, or Outcomes & Retrospective if major
design or scope changes occur.

====================================
Execution Responsibilities
====================================

Your job in this script:

1) Verify that EXEC_PLAN.md, REQUIREMENTS.md, TEST.md, and AGENT_TASKS.md exist.
   - If any are missing, stop internally and do not fabricate files.

2) Coordinate Designer, Frontend Developer, Backend Developer, and Tester using gated handoffs.
3) Ensure that all required artifacts are produced in the correct directories (design, frontend, backend, tests).
4) Update EXEC_PLAN.md sections if needed to reflect execution progress.

====================================
Handoffs (gated by required files)
====================================

Once you have confirmed that EXEC_PLAN.md, REQUIREMENTS.md, TEST.md, and AGENT_TASKS.md exist:

1) Handoff to the Designer with transfer_to_designer_agent and provide:
   - EXEC_PLAN.md
   - REQUIREMENTS.md
   - AGENT_TASKS.md

2) Wait for the Designer to produce /design/design_spec.md.
   - Verify that /design/design_spec.md exists using Codex MCP before proceeding.
   - If missing or clearly misaligned with EXEC_PLAN.md, ask the Designer to correct it and re-check.

3) When design_spec.md exists and is acceptable, hand off in parallel to:
   - Frontend Developer with transfer_to_frontend_developer_agent
     (provide /design/design_spec.md, EXEC_PLAN.md, REQUIREMENTS.md, AGENT_TASKS.md).
   - Backend Developer with transfer_to_backend_developer_agent
     (provide EXEC_PLAN.md, REQUIREMENTS.md, AGENT_TASKS.md).

4) Wait for:
   - /frontend/index.html (and related frontend files), and
   - /backend/server.js (and related backend files).
   Verify both exist and roughly match the intent of EXEC_PLAN.md and REQUIREMENTS.md.

5) When both frontend and backend deliverables exist, hand off to the Tester with transfer_to_tester_agent and provide:
   - EXEC_PLAN.md
   - REQUIREMENTS.md
   - TEST.md
   - AGENT_TASKS.md
   - All relevant outputs from Designer, Frontend, and Backend.

6) Do not advance to the next handoff until the required files for that step are present.
   If something is missing or obviously wrong, request the owning agent to fix it and re-check.

====================================
PM Responsibilities in THIS SCRIPT
====================================

- Coordinate all roles, track file completion, and enforce gating checks.
- Always treat EXEC_PLAN.md as the primary source of truth for intent and behavior.
- Do NOT respond with user-facing status updates; instead, keep handing off until the project is complete.
"""
            ),
            model="gpt-5",
            model_settings=ModelSettings(
                reasoning=Reasoning(effort="medium")
            ),
            handoffs=[designer_agent, frontend_developer_agent, backend_developer_agent, tester_agent],
            mcp_servers=[codex_mcp_server],
        )

        # Wire specialized agents back to PM
        designer_agent.handoffs = [project_manager_agent]
        frontend_developer_agent.handoffs = [project_manager_agent]
        backend_developer_agent.handoffs = [project_manager_agent]
        tester_agent.handoffs = [project_manager_agent]

        # Kick off execution phase
        execution_prompt = """
You are now running the EXECUTION PHASE.

Verify that EXEC_PLAN.md, REQUIREMENTS.md, TEST.md, and AGENT_TASKS.md exist in the current workspace.
If they do, proceed with the handoff sequence described in your instructions to:
- Designer
- Frontend Developer
- Backend Developer
- Tester

Do not recreate the planning documents; only orchestrate execution and update EXEC_PLAN.md's
living sections if needed.
"""

        result = await Runner.run(project_manager_agent, execution_prompt, max_turns=40)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
