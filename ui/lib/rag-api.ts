// RAG-specific API functions

export async function fetchRagBootstrapState() {
  try {
    const response = await fetch("/rag-chatkit/bootstrap");
    if (!response.ok) return null;
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching RAG bootstrap state:", error);
    return null;
  }
}

export async function fetchRagThreadState(threadId: string) {
  try {
    const response = await fetch(`/rag-chatkit/state?thread_id=${threadId}`);
    if (!response.ok) return null;
    const data = await response.json();

    // Add RAG-specific context parsing
    if (data.context) {
      data.context = {
        ...data.context,
        retrieved_chunks: data.context.retrieved_chunks || [],
        sources: data.context.sources || [],
        confidence_score: data.context.confidence_score || 0,
        query_type: data.context.query_type || null,
      };
    }

    return data;
  } catch (error) {
    console.error("Error fetching RAG thread state:", error);
    return null;
  }
}