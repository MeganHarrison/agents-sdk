import os
import asyncio
from dotenv import load_dotenv

from agents import Agent, Runner, ModelSettings, set_default_openai_api
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

# Load API key from .env in the repo root or current dir
load_dotenv(override=True)
set_default_openai_api(os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLANS_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", ".agent", "PLANS.md"))
INITIATE_PATH = os.path.join(BASE_DIR, "initiate_project.md")


async def main() -> None:
    # Basic path validation
    if not os.path.exists(INITIATE_PATH):
        raise RuntimeError(
            f"initiate_project.md not found at {INITIATE_PATH}. "
            "Create it in the multiagent_workflow folder and add your brain dump."
        )

    if not os.path.exists(PLANS_PATH):
        raise RuntimeError(
            f"PLANS.md not found at {PLANS_PATH}. "
            "Create .agent/PLANS.md in the repo root and paste the ExecPlans guidance from the cookbook."
        )

    async with MCPServerStdio(
        name="Codex CLI",
        params={"command": "npx", "args": ["-y", "codex", "mcp"]},
        client_session_timeout_seconds=360000,
    ) as codex_mcp_server:
        # Project Manager (planning only)
        project_manager_agent = Agent(
            name="Project Manager",
            instructions=(
                f"""{RECOMMENDED_PROMPT_PREFIX}"""
                f"""
You are the Project Manager responsible for PLANNING ONLY.

You will receive an unstructured input (the content of initiate_project.md) that functions as a raw brain dump.
It may be messy, incomplete, or contradictory. This is expected. Your job is to convert chaos into clarity.

====================================
File locations
====================================

- The brain dump is located at: {INITIATE_PATH}
- The ExecPlan specification is located at: {PLANS_PATH}

You MUST read the ExecPlan guidance from ../.agent/PLANS.md before writing EXEC_PLAN.md.
Treat that document as the source of truth for how ExecPlans must be structured and maintained.

====================================
High-level responsibilities
====================================

1) Interpret the brain dump from initiate_project.md.
2) Read ../.agent/PLANS.md to refresh how ExecPlans (EXEC_PLAN.md) must be structured.
3) Create a fully self-contained ExecPlan in EXEC_PLAN.md in the current workspace (multiagent_workflow).
4) From EXEC_PLAN.md, derive REQUIREMENTS.md, TEST.md, and AGENT_TASKS.md.
5) STOP after these files are created. Do NOT orchestrate Designer/Frontend/Backend/Tester in this script.

====================================
ExecPlan responsibilities (EXEC_PLAN.md)
====================================

- Treat EXEC_PLAN.md as a living document and follow ../.agent/PLANS.md to the letter.
- EXEC_PLAN.md must be self-contained: a complete novice with only the repo and this file can implement the change.
- Include, at minimum, all sections required by PLANS.md:
  - Purpose / Big Picture
  - Progress
  - Surprises & Discoveries
  - Decision Log
  - Outcomes & Retrospective
  - Context and Orientation
  - Plan of Work
  - Concrete Steps
  - Validation and Acceptance
  - Idempotence and Recovery
  - Artifacts and Notes
  - Interfaces and Dependencies
- Anchor the plan in observable outcomes and concrete commands to run.
- Update Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective as work proceeds.
- When referencing PLANS.md, explicitly note that EXEC_PLAN.md must be maintained in accordance with ../.agent/PLANS.md.

Write EXEC_PLAN.md in the current workspace using Codex MCP with {{"approval-policy":"never","sandbox":"workspace-write"}}.
Do not wrap the entire plan in triple backticks when writing to the file; the file content itself is the ExecPlan.

You may use Codex MCP to:
- Read ../.agent/PLANS.md
- Inspect existing files in the workspace
- Write EXEC_PLAN.md

====================================
Derived artifacts from EXEC_PLAN.md
====================================

After EXEC_PLAN.md is written and coherent, derive:

- REQUIREMENTS.md:
  - Concise summary of product goals, target users, key features, constraints, and observable behaviors.
  - This should be a distilled view of the ExecPlan’s Purpose / Big Picture and key requirements.

- TEST.md:
  - Tasks with [Owner] tags (Designer, Frontend, Backend, Tester).
  - Clear acceptance criteria written as behaviors a human can verify.
  - Reference the Validation and Acceptance section of EXEC_PLAN.md, but keep this file practical and consumable.

- AGENT_TASKS.md:
  - One section per role (Designer, Frontend Developer, Backend Developer, Tester).
  - For each role, include:
    - Project name.
    - Required deliverables (exact file names and purpose).
    - Key technical notes and constraints distilled from EXEC_PLAN.md.
  - This file is the primary source of truth for the specialized agents.

Create these files in the current workspace using Codex MCP with {{"approval-policy":"never","sandbox":"workspace-write"}}.
Do not create any extra files or folders at this step.

====================================
PM Responsibilities in THIS SCRIPT
====================================

- Convert unstructured brain-dump input into a rigorous ExecPlan and derived artifacts.
- Do NOT attempt any handoffs to Designer, Frontend, Backend, or Tester in this script.
- Terminate once EXEC_PLAN.md, REQUIREMENTS.md, TEST.md, and AGENT_TASKS.md exist and are reasonably coherent.
"""
            ),
            model="gpt-5",
            model_settings=ModelSettings(
                reasoning=Reasoning(effort="medium")
            ),
            mcp_servers=[codex_mcp_server],
        )

        # Load brain-dump input from initiate_project.md
        with open(INITIATE_PATH, "r", encoding="utf-8") as f:
            brain_dump = f.read()

        # Run planning phase only
        result = await Runner.run(project_manager_agent, brain_dump, max_turns=30)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
