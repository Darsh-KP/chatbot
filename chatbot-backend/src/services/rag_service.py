

import asyncio
import logging

from langchain_core.documents import Document

from config import settings
from llm import get_llm
from services.vectordb_service import search_collection

LOGGER = logging.getLogger(__name__)

NOT_FOUND_MESSAGE = "I couldn't find that in the Spring documentation."
OFF_TOPIC_MESSAGE = "I can only help with questions about Spring and its documentation."
FALLBACK_SOURCES = 2
NOT_FROM_EXCERPTS = (OFF_TOPIC_MESSAGE.lower(), "excerpts don't cover", "excerpts do not cover", "general knowledge")

SYSTEM_PROMPT = """You are a friendly Spring Framework tutor who explains things to beginners. \
Answer the user's question about Spring clearly and accurately.

How to answer:
- First work out what the user is really asking. Questions are often casual or use different words \
than the documentation. Answer the intent, not just the literal words.
- Use the documentation excerpts below as your main source, and prefer them whenever they cover the question.
- If the excerpts only partly cover the question, or not at all, you may answer from your general \
knowledge of Spring. When you do, say so briefly, for example: "The excerpts don't cover this directly, \
but in general...".
- Use simple, everyday words and short sentences. Explain any technical term the first time you use it, \
as if you were talking to someone new to Spring.
- Include one short real-world analogy from everyday life (for example a restaurant, a library, a post \
office or a school) that matches how the Spring feature really works. Start it with "Think of it like..." \
and keep it to two or three sentences. Use exactly one analogy, never a second one. The analogy only helps \
understanding, so put the exact technical facts in your explanation, not in the analogy.
- Copy class names, annotations, method names and configuration properties exactly. Never invent one. \
If you are not sure a name exists, say you are not sure.
- Keep code examples short and correct, and prefer code taken from the excerpts.
- If the question has nothing to do with Spring or Java development (for example poems, personal \
advice, or anything harmful), reply exactly: "{off_topic}"
- If the question is too vague to answer, ask one short clarifying question instead (no analogy needed).
- Keep the whole answer under about 150 words, not counting code. Do not explain the same example twice.
- Do not write a list of sources or file names. They are added automatically after your answer.

Documentation excerpts:
{context}
"""

REWRITE_PROMPT = """Rewrite the user's question as a short search query for the Spring Framework \
documentation. Use Spring's own terminology where it applies (for example: bean, IoC container, \
dependency injection, annotation, stereotype annotation, component scanning, AOP, transaction). \
Reply with ONLY the search query on one line, with no explanation.

Question: {question}"""


def _display_path(source: str) -> str:
    normalized = source.replace("\\", "/")
    marker = "data/pages/"
    return normalized.split(marker, 1)[1] if marker in normalized else normalized


def _format_context(results: list[tuple[Document, float]]) -> str:
    blocks = []
    for doc, _distance in results:
        title = doc.metadata.get("title", "Untitled")
        path = _display_path(doc.metadata.get("source", ""))
        blocks.append(f"{title} ({path})\n{doc.page_content}")
    return "\n\n".join(blocks)


def _from_excerpts(answer: str) -> bool:
    lowered = answer.lower()
    return not any(marker in lowered for marker in NOT_FROM_EXCERPTS)


def _sources_footer(results: list[tuple[Document, float]]) -> str:
    lines, seen = [], set()
    for doc, _distance in results:
        title = doc.metadata.get("title", "Untitled")
        path = _display_path(doc.metadata.get("source", ""))
        if (title, path) in seen:
            continue  # several chunks of one page: list the page once
        seen.add((title, path))
        lines.append(f"- {title} ({path})" if path else f"- {title}")
        if len(lines) == FALLBACK_SOURCES:
            break
    return "\n\n**Sources**\n" + "\n".join(lines) if lines else ""


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

    if not results:
        LOGGER.warning(
            "The search found nothing in collection %r. Is it empty? Ingest the docs (POST /ingest), "
            "or check RAG_COLLECTION.",
            settings.rag_collection,
        )

    best = min((distance for _, distance in results), default=None)
    too_weak = best is None or (
        settings.rag_max_distance is not None and best > settings.rag_max_distance
    )
    if too_weak:
        return {"answer": NOT_FOUND_MESSAGE, "sources": [], "best_distance": best, "retrieved": len(results)}

    messages = [
        ("system", SYSTEM_PROMPT.format(context=_format_context(results), off_topic=OFF_TOPIC_MESSAGE)),
        ("human", question),
    ]
    reply = await get_llm().ainvoke(messages)

    answer = str(reply.content).strip()
    footer = _sources_footer(results) if _from_excerpts(answer) else ""

    return {
        "answer": answer + footer,
        "sources": _to_sources(results),
        "best_distance": best,
        "retrieved": len(results),
    }