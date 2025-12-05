# RAG Setup Documentation

## What Has Been Implemented

### Frontend Changes (Completed)
1. **New RAG Chat Route**: Created `/rag-chat` route
   - `ui/app/rag-chat/page.tsx` - RAG version of the chat page
   - `ui/components/rag-chatkit-panel.tsx` - RAG-specific ChatKit panel
   - `ui/lib/rag-api.ts` - RAG API functions

2. **Updated Prompts**: Changed from airline to business intelligence:
   - "What were the key decisions from last week's meetings?"
   - "Show me risks identified in ASRS projects"
   - "What tasks are pending for our current projects?"
   - "What patterns do you see in our project delays?"

### Backend Changes (Completed)
1. **Alleato Agent Workflow**: Located in `python-backend/alleato_agent_workflow/`
   - Contains Project, Internal Knowledge Base, and Strategist agents
   - Configured with Supabase MCP connection

2. **RAG Endpoints**: Added to `python-backend/api.py`
   - `/rag-chatkit` - Main chat endpoint
   - `/rag-chatkit/state` - Get conversation state
   - `/rag-chatkit/bootstrap` - Initialize conversation

3. **Updated to Use Documents Table**:
   - Changed from "files" table to "documents" table
   - Ready for vector embeddings retrieval

## Current Status

### ✅ Working Components
- **Environment Variables**: Automatically loaded from `.env` file in root directory
- **Backend Server**: Starts successfully with all RAG endpoints
- **RAG Endpoints**: All three endpoints operational
- **Python Modules**: All imports working correctly

### ✅ Recent Fixes
- **Environment Variables**: Now automatically loaded from `.env` file
- **Supabase Token**: Updated to new token `sbp_c9f4a689e3ea92657771323f0aa31fab6f552b4e`
- **Supabase SDK**: Installed Python SDK as alternative to MCP
- **File Naming**: Renamed `supabase.py` to `supabase_helpers.py` to avoid conflicts

### ⚠️ Current Status
- **MCP Tools**: Temporarily disabled due to 405 Method Not Allowed error
- **Supabase Python SDK**: ✅ Working! Connection verified via `supabase_helpers.py`
- **Documents Table**: Exists but schema differs (missing `chunk_index` column)

## Next Steps

### Immediate Priority
1. **Environment is Ready** - No manual export needed!
   - The `.env` file in root directory contains all variables
   - Python code automatically loads from `.env` using python-dotenv

2. **Verify Documents Table**:
   - Check if `documents` table exists in Supabase
   - Ensure it has `content`, `embedding`, and `metadata` columns
   - Create table if needed (SQL provided in EXEC_PLAN.md)

3. **Test the System**:
   ```bash
   # Start backend
   cd python-backend
   python -m uvicorn api:app --reload --port 8000

   # Start frontend (in another terminal)
   cd ui
   npm run dev

   # Visit http://localhost:3000/rag-chat
   ```

### Phase 1 Remaining Tasks
- [ ] Generate Supabase types for type safety
- [ ] Test actual vector search against documents table
- [ ] Implement basic ingestion pipeline for test data
- [ ] Verify end-to-end retrieval works

## Important Notes

### Guardrails
- Guardrails module is currently optional (not installed)
- System will work without it but with reduced protection

### Authentication
- Requires OPENAI_API_KEY environment variable
- Supabase connection details are hardcoded in alleato_agent_workflow.py

### Testing
- The system is ready for basic testing
- Need to populate documents table with test data
- Vector search functionality depends on having embeddings in the table

## File Structure
```
agents-sdk/
├── python-backend/
│   ├── api.py (main API with RAG endpoints added)
│   ├── alleato_agent_workflow/
│   │   └── alleato_agent_workflow.py (RAG agents)
│   └── .env.example (template for environment variables)
├── ui/
│   ├── app/
│   │   └── rag-chat/
│   │       └── page.tsx (RAG chat page)
│   ├── components/
│   │   └── rag-chatkit-panel.tsx (RAG chat UI)
│   └── lib/
│       └── rag-api.ts (RAG API functions)
└── multiagent_workflow/
    └── EXEC_PLAN.md (implementation plan)