

import asyncio

from langchain_core.documents import Document

from config import settings
from llm import get_llm
from services.vectordb_service import search_collection

NOT_FOUND_MESSAGE = "I couldn't find that in the Spring documentation."

SYSTEM_PROMPT = """You are a friendly Spring Framework tutor who explains things to beginners. \
Answer the user's question about Spring clearly and accurately.

How to answer:
- First work out what the user is really asking. Questions are often casual or use different words \
than the documentation. Answer the intent, not just the literal words.
- Use the documentation excerpts below as your main source, and prefer them whenever they cover the question.
- If the excerpts only partly cover the question, or not at all, you may answer from your general \
knowledge of Spring. When you do, say so briefly, for example: "The Spring Documentation doesn't cover this directly, \
but in general...".
- Use simple, everyday words and short sentences. Explain any technical term the first time you use it, \
as if you were talking to someone new to Spring.
- Include one short real-world analogy from everyday life (for example a restaurant, a library, a post \
office or a school) that matches how the Spring feature really works. Start it with "Think of it like..." \
and keep it to two or three sentences. The analogy only helps understanding, so put the exact technical \
facts in your explanation, not in the analogy.
- Copy class names, annotations, method names and configuration properties exactly. Never invent one. \
If you are not sure a name exists, say you are not sure.
- Keep code examples short and correct, and prefer code taken from the excerpts.
- If the question has nothing to do with Spring or Java development (for example poems, personal \
advice, or anything harmful), politely say you can only help with Spring questions.
- If the question is too vague to answer, ask one short clarifying question instead (no analogy needed).
- Keep the whole answer fairly short. 

Documentation excerpts:
{context}
"""

REWRITE_PROMPT = """Rewrite the user's question as a short search query for the Spring Framework \
documentation. Use Spring's own terminology where it applies (for example: bean, IoC container, \
dependency injection, annotation, stereotype annotation, component scanning, AOP, transaction). \
Reply with ONLY the search query on one line, with no explanation.

Question: {question}"""


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

async def _search_text(question: str) -> str:
    if not settings.rag_rewrite_query:
        return question
    try:
        reply = await get_llm().ainvoke([("human", REWRITE_PROMPT.format(question=question))])
        lines = str(reply.content).strip().splitlines()
        rewritten = lines[0].strip() if lines else ""
    except Exception:
        LOGGER.exception("Query rewrite failed; searching with the original question")
        return question
    return f"{question} {rewritten}".strip() if rewritten else question


async def answer_question(question: str) -> dict:
    if settings.llm_provider == "fake":
        reply = await get_llm().ainvoke([("human", question)])
        return {"answer": str(reply.content).strip(), "sources": [], "best_distance": None, "retrieved": 0}

    search_text = await _search_text(question)

 
    results = await asyncio.to_thread(
        search_collection, settings.rag_collection, search_text, settings.rag_top_k
    )

    best = min((distance for _, distance in results), default=None)
    too_weak = best is None or (
        settings.rag_max_distance is not None and best > settings.rag_max_distance
    )
    if too_weak:
        return {"answer": NOT_FOUND_MESSAGE, "sources": [], "best_distance": best, "retrieved": len(results)}

    messages = [
        ("system", SYSTEM_PROMPT.format(context=_format_context(results))),
        ("human", question),
    ]
    reply = await get_llm().ainvoke(messages)

    return {
        "answer": str(reply.content).strip(),
        "sources": _to_sources(results),
        "best_distance": best,
        "retrieved": len(results),
    }