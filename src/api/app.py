import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessageChunk
from sse_starlette.sse import EventSourceResponse

from src.api.schemas import CitedSource, DiagnosticRequest, DiagnosticResponse
from src.workflow import app as crag_workflow

api = FastAPI(
    title="ABB IRC5 Industrial Diagnostics CRAG API",
    description="Agentic Corrective RAG backend powered by LangGraph and Qdrant hybrid retrieval.",
    version="1.0.0"
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "service": "crag-robotics-diagnostics"}


@api.post("/diagnose", response_model=DiagnosticResponse, tags=["Diagnostics"])
def diagnose_fault(payload: DiagnosticRequest):
    try:
        state = crag_workflow.invoke({
            "query": payload.query,
            "rewritten_query": "",
            "documents": [],
            "filtered_documents": [],
            "generation": "",
            "loop_count": 0
        })

        docs = state.get("filtered_documents") or state.get("documents") or []
        cited_sources = [
            CitedSource(
                chunk_id=doc.metadata.get("chunk_id", "unknown"),
                page=int(doc.metadata.get("page", 0)),
                content=doc.page_content[:300] + "..."
            )
            for doc in docs
        ]

        total_retrieved = len(state.get("documents", []))
        kept = len(docs)
        status = "CORRECT" if kept == total_retrieved and kept > 0 else ("AMBIGUOUS" if kept > 0 else "INCORRECT")

        return DiagnosticResponse(
            query=payload.query,
            rewritten_query=state.get("rewritten_query") or None,
            diagnosis=state.get("generation", "No diagnostic solution could be synthesized."),
            sources=cited_sources,
            retrieval_status=status,
            loop_count=state.get("loop_count", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.post("/diagnose/stream", tags=["Diagnostics"])
async def diagnose_fault_stream(payload: DiagnosticRequest):
    """
    Streams agent lifecycle status and generation tokens in real-time via Server-Sent Events (SSE).
    Emits events:
      - event: node_start (retrieval, grading, rewrite updates)
      - event: token (word-by-word synthesis)
      - event: sources (filtered manual citations)
      - event: done
    """
    async def event_generator():
        initial_state = {
            "query": payload.query,
            "rewritten_query": "",
            "documents": [],
            "filtered_documents": [],
            "generation": "",
            "loop_count": 0
        }

        # Stream langgraph events
        async for event in crag_workflow.astream_events(initial_state, version="v2"):
            kind = event["event"]
            # Emit node transitions for ui progress indicators
            if kind == "on_chain_start":
                event_name = event.get("name", "")

                if event_name in [
                    "retrieve",
                    "grade_documents",
                    "rewrite_query",
                    "generate",
                ]:
                    clean_name = (
                        "rewrite"
                        if event_name == "rewrite_query"
                        else event_name
                    )

                    yield {
                        "event": "status",
                        "data": json.dumps({
                            "node": clean_name,
                            "message": f"Executing node: {clean_name}"
                        })
                    }

            # Stream generation tokens as they leave the llm inside the 'generate' node
            elif kind == "on_chat_model_stream":
                node_name = event.get("metadata", {}).get("langgraph_node", "")
                if node_name in ["generate", "generate_node"]:
                    chunk = event["data"]["chunk"]
                    content = chunk.content if isinstance(chunk, AIMessageChunk) else getattr(chunk, "text", "")
                    if content:
                        yield {
                            "event": "token",
                            "data": json.dumps({"token": content})
                        }

            elif kind == "on_chain_end" and event.get("name") == "grade_documents":
                output = event["data"].get("output", {})

                documents = output.get("documents", [])
                filtered_documents = output.get("filtered_documents", [])
                retrieved = len(documents)
                relevant = len(filtered_documents)

                if relevant == 0:
                    grade_verdict = "INCORRECT"

                elif relevant < retrieved:
                    grade_verdict = "AMBIGUOUS"

                else:
                    grade_verdict = "CORRECT"

                yield {
                    "event": "grade",
                    "data": json.dumps({
                        "verdict": grade_verdict,
                        "relevant": relevant,
                        "retrieved": retrieved
                    })
                }
            # Capture the final state when the graph finishes to stream source references
            elif kind == "on_chain_end" and event.get("name") == "LangGraph":
                final_output = event["data"].get("output", {})
                filtered = final_output.get("filtered_documents")
                docs = filtered if filtered is not None else final_output.get("documents", [])
                if not docs:
                    fallback_text = final_output.get("generation", "")
                    if fallback_text:
                        yield {
                            "event": "token",
                            "data": json.dumps({"token": fallback_text})
                        }

                sources = [
                    {
                        "chunk_id": d.metadata.get("chunk_id", "unknown"),
                        "page": int(d.metadata.get("page", 0)),
                        "snippet": d.page_content[:200] + "..."
                    }
                    for d in docs
                ]
                yield {
                    "event": "sources",
                    "data": json.dumps({"sources": sources})
                }

        # Terminate the stream
        yield {
            "event": "done",
            "data": json.dumps({"status": "complete"})
        }

    return EventSourceResponse(event_generator())