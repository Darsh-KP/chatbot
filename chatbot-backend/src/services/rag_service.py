

import asyncio

from langchain_core.documents import Document

from config import settings
from llm import get_llm
from services.vectordb_service import search_collection

NOT_FOUND_MESSAGE = "I couldn't find that in the Spring documentation."

SYSTEM_PROMPT = """You are a helpful assistant that answers questions about the Spring Framework \
using ONLY the documentation excerpts provided below.

Rules:
- Use only the information in the excerpts. Do not use outside knowledge.
- If the excerpts do not contain the answer, reply exactly: "{not_found}"
- If the question is not about Spring or its documentation (for example poems, personal advice, \
or anything harmful), politely say you can only help with questions about the Spring documentation.
- Copy class names, annotations, method names and configuration properties exactly as they appear \
in the excerpts. Never invent one.
- Keep code examples exactly as written in the excerpts.
- Be friendly and concise, and mention which section (title) your answer comes from.

Documentation excerpts:
{context}
"""


def _display_path(source: str) -> str:
    """Show 'core/aop.adoc' instead of a full path from whichever machine ran the ingestion."""
    normalized = source.replace("\\", "/")
    marker = "data/pages/"
    return normalized.split(marker, 1)[1] if marker in normalized else normalized


def _format_context(results: list[tuple[Document, float]]) -> str:
    blocks = []
    for i, (doc, _distance) in enumerate(results, start=1):
        title = doc.metadata.get("title", "Untitled")
        path = _display_path(doc.metadata.get("source", ""))
        blocks.append(f"[Excerpt {i}: {title} ({path})]\n{doc.page_content}")
    return "\n\n".join(blocks)


def _to_sources(results: list[tuple[Document, float]]) -> list[dict]:
    return [
        {
            "title": doc.metadata.get("title", "Untitled"),
            "path": _display_path(doc.metadata.get("source", "")),
            "distance": round(float(distance), 4),
            "snippet": doc.page_content[:200],
        }
        for doc, distance in results
    ]


async def answer_question(question: str) -> dict:
    if settings.llm_provider == "fake":
        # Fake mode must work with no Ollama at all. Retrieval needs the embedding model,
        # so skip it and return the canned reply (handy for building the UI and API).
        reply = await get_llm().ainvoke([("human", question)])
        return {"answer": str(reply.content).strip(), "sources": [], "best_distance": None, "retrieved": 0}

    # Embedding + vector search are blocking calls, so run them off the event loop.
    results = await asyncio.to_thread(
        search_collection, settings.rag_collection, question, settings.rag_top_k
    )

    best = min((distance for _, distance in results), default=None)
    too_weak = best is None or (
        settings.rag_max_distance is not None and best > settings.rag_max_distance
    )
    if too_weak:
        # Nothing relevant found: don't even call the LLM, so it can't make something up.
        return {"answer": NOT_FOUND_MESSAGE, "sources": [], "best_distance": best, "retrieved": len(results)}

    messages = [
        ("system", SYSTEM_PROMPT.format(not_found=NOT_FOUND_MESSAGE, context=_format_context(results))),
        ("human", question),
    ]
    reply = await get_llm().ainvoke(messages)

    return {
        "answer": str(reply.content).strip(),
        "sources": _to_sources(results),
        "best_distance": best,
        "retrieved": len(results),
    }