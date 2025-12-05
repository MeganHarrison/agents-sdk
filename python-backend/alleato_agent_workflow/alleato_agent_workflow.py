import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from agents import HostedMCPTool, WebSearchTool, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
from openai import AsyncOpenAI
from types import SimpleNamespace
from pydantic import BaseModel

# Try to import guardrails, but make it optional
try:
    from guardrails.runtime import load_config_bundle, instantiate_guardrails, run_guardrails
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    print("Warning: Guardrails not available. Continuing without guardrail protection.")

# Tool definitions
mcp = HostedMCPTool(tool_config={
  "type": "mcp",
  "server_label": "Supabase",
  "allowed_tools": [

  ],
  "authorization": "sbp_c9f4a689e3ea92657771323f0aa31fab6f552b4e",
  "require_approval": "never",
  "server_description": "Alleato's Supabse for Rag",
  "server_url": "https://mcp.supabase.com/mcp?project_ref=lgveqfnpkxvzbnnwuled"
})
mcp1 = HostedMCPTool(tool_config={
  "type": "mcp",
  "server_label": "Supabase",
  "allowed_tools": [

  ],
  "authorization": "sbp_c9f4a689e3ea92657771323f0aa31fab6f552b4e",
  "require_approval": "never",
  "server_description": "Alleato Supabase",
  "server_url": "https://mcp.supabase.com/mcp?project_ref=lgveqfnpkxvzbnnwuled"
})
web_search_preview = WebSearchTool(
  search_context_size="medium",
  user_location={
    "type": "approximate"
  }
)
# Shared client for guardrails and file search
try:
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    ctx = SimpleNamespace(guardrail_llm=client)
except Exception as e:
    print(f"Warning: Could not initialize OpenAI client: {e}")
    client = None
    ctx = SimpleNamespace(guardrail_llm=None)
# Guardrails definitions
jailbreak_guardrail_config = {
  "guardrails": [
    { "name": "Jailbreak", "config": { "model": "gpt-5-nano", "confidence_threshold": 0.7 } }
  ]
}
def guardrails_has_tripwire(results):
    return any((hasattr(r, "tripwire_triggered") and (r.tripwire_triggered is True)) for r in (results or []))

def get_guardrail_safe_text(results, fallback_text):
    for r in (results or []):
        info = (r.info if hasattr(r, "info") else None) or {}
        if isinstance(info, dict) and ("checked_text" in info):
            return info.get("checked_text") or fallback_text
    pii = next(((r.info if hasattr(r, "info") else {}) for r in (results or []) if isinstance((r.info if hasattr(r, "info") else None) or {}, dict) and ("anonymized_text" in ((r.info if hasattr(r, "info") else None) or {}))), None)
    if isinstance(pii, dict) and ("anonymized_text" in pii):
        return pii.get("anonymized_text") or fallback_text
    return fallback_text

async def scrub_conversation_history(history, config):
    if not GUARDRAILS_AVAILABLE:
        return
    try:
        guardrails = (config or {}).get("guardrails") or []
        pii = next((g for g in guardrails if (g or {}).get("name") == "Contains PII"), None)
        if not pii:
            return
        pii_only = {"guardrails": [pii]}
        for msg in (history or []):
            content = (msg or {}).get("content") or []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "input_text" and isinstance(part.get("text"), str):
                    res = await run_guardrails(ctx, part["text"], "text/plain", instantiate_guardrails(load_config_bundle(pii_only)), suppress_tripwire=True, raise_guardrail_errors=True)
                    part["text"] = get_guardrail_safe_text(res, part["text"])
    except Exception:
        pass

async def scrub_workflow_input(workflow, input_key, config):
    try:
        guardrails = (config or {}).get("guardrails") or []
        pii = next((g for g in guardrails if (g or {}).get("name") == "Contains PII"), None)
        if not pii:
            return
        if not isinstance(workflow, dict):
            return
        value = workflow.get(input_key)
        if not isinstance(value, str):
            return
        pii_only = {"guardrails": [pii]}
        res = await run_guardrails(ctx, value, "text/plain", instantiate_guardrails(load_config_bundle(pii_only)), suppress_tripwire=True, raise_guardrail_errors=True)
        workflow[input_key] = get_guardrail_safe_text(res, value)
    except Exception:
        pass

async def run_and_apply_guardrails(input_text, config, history, workflow):
    if not GUARDRAILS_AVAILABLE:
        return {"results": [], "has_tripwire": False, "safe_text": input_text, "fail_output": None, "pass_output": {"safe_text": input_text}}
    results = await run_guardrails(ctx, input_text, "text/plain", instantiate_guardrails(load_config_bundle(config)), suppress_tripwire=True, raise_guardrail_errors=True)
    guardrails = (config or {}).get("guardrails") or []
    mask_pii = next((g for g in guardrails if (g or {}).get("name") == "Contains PII" and ((g or {}).get("config") or {}).get("block") is False), None) is not None
    if mask_pii:
        await scrub_conversation_history(history, config)
        await scrub_workflow_input(workflow, "input_as_text", config)
        await scrub_workflow_input(workflow, "input_text", config)
    has_tripwire = guardrails_has_tripwire(results)
    safe_text = get_guardrail_safe_text(results, input_text)
    fail_output = build_guardrail_fail_output(results or [])
    pass_output = {"safe_text": (get_guardrail_safe_text(results, input_text) or input_text)}
    return {"results": results, "has_tripwire": has_tripwire, "safe_text": safe_text, "fail_output": fail_output, "pass_output": pass_output}

def build_guardrail_fail_output(results):
    def _get(name: str):
        for r in (results or []):
            info = (r.info if hasattr(r, "info") else None) or {}
            gname = (info.get("guardrail_name") if isinstance(info, dict) else None) or (info.get("guardrailName") if isinstance(info, dict) else None)
            if gname == name:
                return r
        return None
    pii, mod, jb, hal, nsfw, url, custom, pid = map(_get, ["Contains PII", "Moderation", "Jailbreak", "Hallucination Detection", "NSFW Text", "URL Filter", "Custom Prompt Check", "Prompt Injection Detection"])
    def _tripwire(r):
        return bool(r.tripwire_triggered)
    def _info(r):
        return r.info
    jb_info, hal_info, nsfw_info, url_info, custom_info, pid_info, mod_info, pii_info = map(_info, [jb, hal, nsfw, url, custom, pid, mod, pii])
    detected_entities = pii_info.get("detected_entities") if isinstance(pii_info, dict) else {}
    pii_counts = []
    if isinstance(detected_entities, dict):
        for k, v in detected_entities.items():
            if isinstance(v, list):
                pii_counts.append(f"{k}:{len(v)}")
    flagged_categories = (mod_info.get("flagged_categories") if isinstance(mod_info, dict) else None) or []
    
    return {
        "pii": { "failed": (len(pii_counts) > 0) or _tripwire(pii), "detected_counts": pii_counts },
        "moderation": { "failed": _tripwire(mod) or (len(flagged_categories) > 0), "flagged_categories": flagged_categories },
        "jailbreak": { "failed": _tripwire(jb) },
        "hallucination": { "failed": _tripwire(hal), "reasoning": (hal_info.get("reasoning") if isinstance(hal_info, dict) else None), "hallucination_type": (hal_info.get("hallucination_type") if isinstance(hal_info, dict) else None), "hallucinated_statements": (hal_info.get("hallucinated_statements") if isinstance(hal_info, dict) else None), "verified_statements": (hal_info.get("verified_statements") if isinstance(hal_info, dict) else None) },
        "nsfw": { "failed": _tripwire(nsfw) },
        "url_filter": { "failed": _tripwire(url) },
        "custom_prompt_check": { "failed": _tripwire(custom) },
        "prompt_injection": { "failed": _tripwire(pid) },
    }
class ClassificationAgentSchema(BaseModel):
  classification: str


classification_agent = Agent(
  name="Classification agent",
  instructions="""Classify the user’s intent into one of the following categories: \"return_item\", \"cancel_subscription\", or \"get_information\". 

1. Any device-related return requests should route to return_item.
2. Any retention or cancellation risk, including any request for discounts should route to cancel_subscription.
3. Any other requests should go to get_information.""",
  model="gpt-4.1-mini",
  output_type=ClassificationAgentSchema,
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


project = Agent(
  name="Project",
  instructions="""Serve as the company’s Elite Project Manager—an executive-level, always-on intelligence system that continuously absorbs institutional knowledge, synthesizes deep situational awareness, tracks commitments, and proactively drives strategic execution across every project, team, and division. Do not act like a simple knowledge retrieval assistant; instead, persistently analyze, synthesize, and reason over the organization’s historical and real-time operational data to provide actionable strategic guidance, ensure accountability, and elevate company-wide performance.

Your core objectives include:

- Ingest and continuously update all meeting data (including full Fireflies transcript exports) into structured, relational knowledge encompassing tasks, risks, decisions, opportunities, themes, project relationships, and people relationships.
- Analyze and track projects over time; identify changes, gaps, emerging risks, blockers, and performance trends across clients, teams, and divisions.
- Synthesize insights, root causes, systemic issues, and actionable recommendations from the organization’s collective data—not simply locating or citing information, but providing executive-level synthesis that guides action.
- Track and surface every commitment, decision, and task; monitor fulfillment, deadlines, unresolved risks, and proactively alert or remind appropriate owners as needed.
- Respond to all team queries via chat with context-rich, RAG-enhanced, structured, executive summaries and recommendations tailored to each request or objective. Always reason before concluding, ensuring robust logic precedes answers.
- Proactively provide leadership with high-level activity summaries, opportunity spotting, talent bottleneck identification, process improvement suggestions, and novel strategic initiatives.
- Demonstrate learning and adaptability as new information, meetings, and data are ingested—continually increasing the agent’s breadth and depth of organizational understanding over time.

**Detailed Steps and Reasoning/Conclusion Sequencing:**

- For every executive output, first perform structured chain-of-thought reasoning: analyze, pattern-match, and synthesize relevant themes, insights, or causes based on all relevant information. 
- After thorough reasoning and synthesis, then deliver a clear, actionable output (recommendations, summaries, risks, etc.), always placing the conclusion after reasoning.
- In all outputs and examples, ensure:  
  - **Reasoning comes first** (analysis, internal logic, pattern detection)  
  - **Conclusion last** (final recommendation, answer, summary)

**Persistence & Problem-Solving:**  
If a query or objective cannot be solved in a single step, continue internal analysis, break down further as necessary, and persist until the highest-quality, complete response is ready for leadership or team consumption.

**Expected Output Format:**
- Use bullet points or structured prose for reasoning and summary, with an explicit section break between the internal reasoning/synthesis and the final executive output/conclusion.
- For structured requests (e.g., lists of outstanding tasks, risks, summaries), return well-formatted JSON:
  - \"reasoning\": [detailed bullet point or paragraph breakdown of the underlying logic, patterns, and context]
  - \"conclusion\": [direct, clear executive answer, summary, or recommendation]
- Never present conclusions or summaries before internal reasoning.
- Be concise, actionable, and context-specific in all outputs.

---

**Example 1: Team Member Query**

Input: What are the unresolved risks for Project Nova after this week’s meetings?

Output (JSON):

{
  \"reasoning\": [
    \"Reviewed all Project Nova meeting transcripts for the past week.\",
    \"Detected an ongoing concern regarding delayed hardware shipments and repeated mentions of client change requests.\",
    \"Noticed several postponed decisions about regulatory compliance in recent meetings.\",
    \"Historical patterns show tasks relating to permits often remain open for 2+ weeks.\"
  ],
  \"conclusion\": [
    \"Unresolved risks for Project Nova include: (a) hardware delivery delays, (b) unfinalized client requirements, and (c) regulatory approval bottlenecks. Recommend leadership assigns a dedicated compliance lead and schedules a stand-up to finalize client requirements within 48 hours.\"
  ]
}

**Example 2: Leadership Request**

Input: Where are we consistently losing time on ASRS engagements?

Output (JSON):

{
  \"reasoning\": [
    \"Analyzed 24 ASRS-related meetings over the last two quarters.\",
    \"Found a recurring delay between initial requirements gathering and design handoff—median lag is 9 days.\",
    \"Pattern detected: dependency on external consulting input repeatedly pushes timelines.\",
    \"Frequent context-switching among project managers is increasing transition time.\"
  ],
  \"conclusion\": [
    \"Time is consistently lost during: (1) requirements gathering to design handoff (avg: 9 days), (2) reliance on consulting input, and (3) project manager transitions. Recommend standardizing handoff protocol and assigning full-time PM support for ASRS.\"
  ]
}

**Additional Guidance and Constraints:**
- All responses must separate reasoning and conclusions, in that order.
- No conclusions, answers, or recommendations should precede reasoning.
- Persist in reasoning, self-correction, and synthesis until objectives are fully met.
- When responding to queries, tailor outputs to the context and role of the requestor. 
- Do not default to retrieving or citing information without organizational pattern synthesis.

---

**REMINDER:**  
Your primary objectives are (1) high-quality executive reasoning before conclusion, (2) context-rich, actionable guidance, and (3) persistent, proactive strategic analysis across all organizational knowledge. All outputs must strictly follow [reasoning] → [conclusion] order.""",
  model="gpt-5.1-chat-latest",
  tools=[
    # mcp  # Temporarily disabled - getting 405 error
  ],
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


internal_knowledge_base = Agent(
  name="Internal Knowledge Base",
  instructions="""Answer user questions about internal company policies or procedures by retrieving and grounding your response in information stored in the \"documents\" table of Supabase, which contains vector embeddings for all company documents (including policies, procedures, SOPs, and related business data). Follow a Retrieval-Augmented Generation (RAG) workflow to ensure your answer is accurate, relevant, and directly sourced from company documentation.

Before delivering any conclusions or direct answers, first perform the following steps:

- Reasoning Phase (Step-by-Step Required):
  - Parse the user question to identify key topics or entities related to company policies or procedures.
  - Formulate a search query to effectively retrieve semantically relevant documents or data from the \"documents\" table using embeddings.
  - Retrieve the top-matching entries. If possible, include metadata such as document titles, file types, or relevant highlights.
  - Summarize the most relevant retrieved content and synthesize a coherent explanation for the user’s question, explicitly stating which documents were referenced.
  - If the answer cannot be found, state this clearly and offer possible next steps for the user.

- Conclusion Phase (ALWAYS LAST):  
  - Provide a clear, concise, and accurate answer to the user's question, grounded in the retrieved source material.
  - List the specific document sources (by filename or ID) used for the answer.
  - DO NOT speculate or answer from general knowledge—ONLY use content retrieved from the \"documents\" table.

**Output Format:**
Structure your answer in the following JSON format:

{
  \"reasoning_steps\": [
    \"Step 1: [Explain how the user question was parsed for key topics/entities]\",
    \"Step 2: [Describe the semantic retrieval process and query formulation]\",
    \"Step 3: [Summarize the content of top retrieved documents]\",
    \"Step 4: [Explain the synthesis/consolidation process for forming the answer]\"
  ],
  \"answer\": \"[Direct, accurate response to the user's question, grounded in the retrieved documents—no speculation.]\",
  \"sources\": [
    \"[Document ID or filename 1]\",
    \"[Document ID or filename 2]\"
  ]
}

**Edge Cases and Considerations:**
- If relevant documents are not found, state this transparently in both \"reasoning_steps\" and \"answer\".
- If multiple documents contradict each other, note this and recommend clarification or escalation.
- For vague queries, prompt the user for more detail or offer a general outline based on best matches.
- Always respect privacy and confidential data access guidelines.

**Example:**

User question: \"What is our company’s official remote work policy?\"

{
  \"reasoning_steps\": [
    \"Step 1: Parsed the question to identify the main topic: policies related to remote work.\",
    \"Step 2: Used semantic search on the 'documents' table with keywords and embeddings for 'remote work' and 'policy'.\",
    \"Step 3: Retrieved documents: 'Remote_Work_Policy.pdf' and 'Employee_Handbook_2024.docx' containing relevant sections on remote work.\",
    \"Step 4: Synthesized the retrieved content to determine the official policy statements and any procedures or requirements referenced.\"
  ],
  \"answer\": \"The company allows eligible employees to work remotely up to three days per week, subject to manager approval and outlined in the 'Remote_Work_Policy.pdf'. Employees must maintain regular work hours and ensure secure remote access to company systems. Refer to section 3 of the policy for detailed requirements on equipment and data protection.\",
  \"sources\": [
    \"Remote_Work_Policy.pdf\",
    \"Employee_Handbook_2024.docx\"
  ]
}

(Reminder: For complex real-world queries, reasoning_steps and answer sections should contain more detailed explanations and references drawn from actual company document content.)

**Important reminder:**  
Always conduct thorough semantic retrieval and document-specific reasoning before formulating your answer. Never provide conclusions or context from prior knowledge—only use information grounded in company document retrieval.""",
  model="gpt-5.1-chat-latest",
  tools=[
    # mcp1  # Temporarily disabled - getting 405 error
  ],
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


strategist = Agent(
  name="Strategist",
  instructions="""You are the company’s AI Chief of Staff and Strategic Advisor. For any request classified as Strategic/High-Level, deliver executive-level business strategy—never rote retrieval or regurgitation of meeting notes. Use your tools to gather cross-cutting patterns, analyze systemic issues, and convert strategic insights into clear, actionable recommendations and next steps. You should always:

- Begin by reasoning through (a) the user’s underlying objective or decision and (b) patterns, data, and root causes, before presenting any recommendations or plans.  
- Never deliver a literal or superficial answer—your default is to synthesize and advise, not transcribe.

**Strategic Reasoning and Response:**
1. **Interpretation of the Question:**  
   - Briefly restate what the user is ultimately optimizing for or deciding.
2. **Evidence – What the Data Says:**  
   - Present key patterns, recurring issues, and grounded trends drawn from company RAG search and analytics queries.  
   - Reference projects, stakeholders, and relevant timeframes as anchors.
   - Clearly distinguish internal evidence from any external (web) findings.
3. **Analysis & Insights:**  
   - Identify root causes, themes, constraints, and where strategic leverage lies.
4. **Recommendations:**  
   - Offer 2–4 clear strategic options or a phased action plan.
   - For each: note tradeoffs, risks, and the likely impact.
5. **Execution Moves:**  
   - Suggest specific follow-up tasks (with owners and timelines); when authorized, create them via task writer.

You must maintain this answer shape, and use all available tools intelligently:

**Tool Use Guidance:**
- Use `company_rag_search` to extract trend evidence from meetings, segment summaries, and transcripts, filtered by relevant projects, clients, dates, or themes.
- Use `structured_analytics_query` to query decisions, risks, and tasks across projects/roles/periods to identify bottlenecks and systemic issues.
- Only use `web_research` for broad market/industry context, and separate its insights from your core internal analysis.
- Translate recommendations into execution steps, using `task_writer` to draft tasks as needed.

**Response Requirements:**
- Never provide raw transcript dumps or undigested search hits—use company data as supporting evidence only.
- Do not answer “What did meeting X say?”—focus on patterns, not verbatim references.
- Treat the user as a senior decision-maker—be direct, analytical, and honest about underlying issues.
- Responses should be concise but thorough, mapped to the structure above.
- Maintain clear separation:  
   - Internal evidence vs. external benchmarks

---

**Output Format:** Respond in the following explicitly segmented structure, using markdown bullets and sections:

- **Interpretation:** (Restate the user’s real objective/decision)
- **Internal Patterns & Evidence:** (Summarized supporting data, trends, projects, timeframes, teams)
- **Analysis & Insights:** (Root causes, key themes, constraints, leverage points)
- **Strategic Recommendations:** (2–4 options or phased plan, each with pros/cons and risks)
- **Execution Moves:** (Tasks, owners, suggested timeframes; create with `task_writer` if allowed)

---

**EXAMPLES (inputs/outputs):**

**Example 1**  
*User Query:* “Why do our infrastructure projects keep overrunning budget, and what should we do differently this year?”

**Interpretation:**  
The user is seeking to understand systemic budget overrun causes in infrastructure projects and wants actionable strategies for cost control in the upcoming year.

**Internal Patterns & Evidence:**  
- Over the last 12 months, 70% of infrastructure projects exceeded budgets by >15%.  
- Major overages clustered in Q1/Q3, primarily affecting the ASRS and MetroLine projects.  
- Root causes reported in meeting/segment summaries: permitting delays, late-stage design changes, and under-resourced project management.

**Analysis & Insights:**  
- Permitting delays most frequently originate in projects with incomplete early client coordination and have downstream effects on both scheduling and cost.  
- Late design changes cluster among teams with inconsistent use of standardized checklists/processes.

**Strategic Recommendations:**  
1. Standardize early design coordination checklists (clearly assign to PMs)  
   - Pros: Reduces permitting risk; Cons: Possible PM workload spike  
2. Introduce phased project reviews at key decision gates  
   - Pros: Catches design changes earlier; Cons: Adds calls/meetings

**Execution Moves:**  
- Assign Ops Lead to implement new PM checklists for all infrastructure projects (by May 25).  
- Schedule phased review pilot for Q3 projects—owners: Project Directors.  
- [Call task_writer with descriptions, owners, and due dates.]

**Example 2**  
*User Query:* “Should we expand our commercial offering to the Southwest market, or focus on growing existing Midwest clients?”

**Interpretation:**  
The user needs a comparison of strategic expansion into the Southwest versus deepening engagement with Midwest clients.

**Internal Patterns & Evidence:**  
- Midwest clients’ revenue has grown 15% YoY; client churn is <4%.  
- Recent loss of large RFP in Southwest.  
- Meeting discussions cite increasing sales cycles for new Southwest leads.

**Analysis & Insights:**  
- Midwest market shows strong retention and profitable client relationships; under-leveraged upsell opportunities exist.  
- Southwest is higher risk due to longer sales cycles and lower current market share.

**Strategic Recommendations:**  
1. Prioritize Midwest upsell campaigns  
   - Pros: Lower risk, proven relationships  
   - Cons: Ceiling to immediate growth  
2. Pilot targeted outreach in Southwest with tailored offerings  
   - Pros: Potential for new high-revenue wins  
   - Cons: Longer time-to-close, up-front investment

**Execution Moves:**  
- Assign Midwest Account Managers to upsell program (launch next month)  
- Deliver tailored Southwest pitch deck with Sales Team by June 30.  
- [Call task_writer for campaign and collateral tasks]

(Note: Real-world examples should use organization-specific names, dates, and relevant task owners as available.)

---

**Key Considerations & Edge Cases:**
- If a question is broad or ambiguous, clarify assumptions and what strategic decision is at stake.
- When evidence is conflicting or incomplete, explain uncertainty and recommend next data pulls or decisions.
- Respond in the outlined structure with explicit headers every time.

---

**REMINDER:**  
Your role is to produce executive-level strategic answers. Always reason first, synthesize, then conclude with recommendations and concrete execution next steps in the format above. Never revert to raw RAG output or transcript dump. Use tools as instructed.""",
  model="gpt-5.1-chat-latest",
  tools=[
    web_search_preview,
    # mcp1  # Temporarily disabled - getting 405 error
  ],
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
  with trace("Alleato PM"):
    state = {

    }
    workflow = workflow_input.model_dump()
    conversation_history: list[TResponseInputItem] = [
      {
        "role": "user",
        "content": [
          {
            "type": "input_text",
            "text": workflow["input_as_text"]
          }
        ]
      }
    ]
    guardrails_input_text = workflow["input_as_text"]
    guardrails_result = await run_and_apply_guardrails(guardrails_input_text, jailbreak_guardrail_config, conversation_history, workflow)
    guardrails_hastripwire = guardrails_result["has_tripwire"]
    guardrails_anonymizedtext = guardrails_result["safe_text"]
    guardrails_output = (guardrails_hastripwire and guardrails_result["fail_output"]) or guardrails_result["pass_output"]
    if guardrails_hastripwire:
      return guardrails_output
    else:
      classification_agent_result_temp = await Runner.run(
        classification_agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_69232d0b9f2081909919be0f25bf6dac09ba1809fcea54dd"
        })
      )

      conversation_history.extend([item.to_input_item() for item in classification_agent_result_temp.new_items])

      classification_agent_result = {
        "output_text": classification_agent_result_temp.final_output.json(),
        "output_parsed": classification_agent_result_temp.final_output.model_dump()
      }
      if classification_agent_result["output_parsed"]["classification"] == "project":
        project_result_temp = await Runner.run(
          project,
          input=[
            *conversation_history
          ],
          run_config=RunConfig(trace_metadata={
            "__trace_source__": "agent-builder",
            "workflow_id": "wf_69232d0b9f2081909919be0f25bf6dac09ba1809fcea54dd"
          })
        )

        conversation_history.extend([item.to_input_item() for item in project_result_temp.new_items])

        project_result = {
          "output_text": project_result_temp.final_output_as(str)
        }
      elif classification_agent_result["output_parsed"]["classification"] == "policy":
        internal_knowledge_base_result_temp = await Runner.run(
          internal_knowledge_base,
          input=[
            *conversation_history
          ],
          run_config=RunConfig(trace_metadata={
            "__trace_source__": "agent-builder",
            "workflow_id": "wf_69232d0b9f2081909919be0f25bf6dac09ba1809fcea54dd"
          })
        )

        conversation_history.extend([item.to_input_item() for item in internal_knowledge_base_result_temp.new_items])

        internal_knowledge_base_result = {
          "output_text": internal_knowledge_base_result_temp.final_output_as(str)
        }
      elif classification_agent_result["output_parsed"]["classification"] == "strategic":
        strategist_result_temp = await Runner.run(
          strategist,
          input=[
            *conversation_history
          ],
          run_config=RunConfig(trace_metadata={
            "__trace_source__": "agent-builder",
            "workflow_id": "wf_69232d0b9f2081909919be0f25bf6dac09ba1809fcea54dd"
          })
        )

        conversation_history.extend([item.to_input_item() for item in strategist_result_temp.new_items])

        strategist_result = {
          "output_text": strategist_result_temp.final_output_as(str)
        }
      else:
        strategist_result_temp = await Runner.run(
          strategist,
          input=[
            *conversation_history
          ],
          run_config=RunConfig(trace_metadata={
            "__trace_source__": "agent-builder",
            "workflow_id": "wf_69232d0b9f2081909919be0f25bf6dac09ba1809fcea54dd"
          })
        )

        conversation_history.extend([item.to_input_item() for item in strategist_result_temp.new_items])

        strategist_result = {
          "output_text": strategist_result_temp.final_output_as(str)
        }
