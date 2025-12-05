# Initiate Project

This project is currently a cloned version of the Customer Service Agent Template from OpenAI's github: https://github.com/openai/openai-cs-agents-demo.git.

```
This repository contains a demo of a Customer Service Agent interface built on top of the OpenAI Agents SDK. It is composed of two parts:

1. A python backend that handles the agent orchestration logic, implementing the Agents SDK customer service example

2. A Next.js UI allowing the visualization of the agent orchestration process and providing a chat interface utilizing Chatkit UI.
```

The goal is see you utilize this repo as a starter template and customize it for our unique project. This allows a lot of the initial set up to already be in place.

The chat needs to be modified to become an ai agent that serves as the ultimate project manager and business strategist for Alleato.

Every meeting transcript will be exported from fireflies using the fireflies api key and added to a Supabase storage bucket and added to a table named document_metadata. 

This table will have columns for all of the metadata such as fireflies id, summary, participants and full content from the transcript, and link to the file in the Supabase storage bucket.

These files will also be vectorized abs embeddings saved in the documents table in Supabase. 

We have over three years of meeting transcripts saved this way. The goal is for the AI agent to know practically everything they’re possibly is about the company and all of the past and current projects that way it can identify patterns. Look for opportunities for improvement identify risks, Create tasks and follow up with employees as needed generate insights and provide extremely valuable information to the leadership team. there also needs to be a chat interface that allows team members to chat directly with the agent that will utilize the embedding and perform rag to respond intelligently.

Instead of acting like a simple knowledge retrieval bot, this agent becomes the central intelligence layer of the business, capable of:

- Understanding the full history of the company
- Detecting patterns, risks, and opportunities across years of meetings
- Providing strategic guidance to leadership
- Tracking commitments, decisions, and tasks
- Ensuring follow-through and accountability
- Supporting team members through a conversational interface
- Becoming the “memory” and “thinking partner” of the entire organization

## Important Notes

- One of the most important tasks will be planning and implementing the best chunking and retrieval strategy possible that will allow the chat agent to provide immense value.

- The meeting transcripts will not have a project identified by default so there needs to be a way for the AI to do its best to determine the correct project from the table named "projects" and have the phase set to "Current". This can be done by reviewing the file name, participants, and content from the transcript.

- There will be a page with a table showing all projects. Each project will link to an individual project homepage that shows the associated meetings, tasks, AI generated insights, ect.

- AI will create and assign tasks to employees based on the transcripts.

## Recap

- Review current codebase to identify what has already been created.

- Use Supabase as the vector store.

- Transcript markdown Files saved to Supabase storage bucket: meetings
- Files added to Supabase document_metadata table
- Embeddings created and saved to Supabase documents table