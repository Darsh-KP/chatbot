import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

# Allow imports from the src directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from services import rag_service

QUESTION = "what are the things called to classify a class as something?"
DOCS = [(Document(page_content="@Component is a stereotype...", metadata={"title": "Classpath Scanning"}), 0.5)]


class FakeLLM:
    """Stands in for the chat model; records every call so tests can inspect them."""

    def __init__(self, fail_on_rewrite=False):
        self.calls = []
        self.fail_on_rewrite = fail_on_rewrite

    async def ainvoke(self, messages):
        self.calls.append(messages)
        if messages[0][1].startswith("Rewrite the user's question"):
            if self.fail_on_rewrite:
                raise TimeoutError("model timed out")
            return SimpleNamespace(content="annotation stereotype component\nextra line")
        return SimpleNamespace(content="  The answer.  ")


@pytest.fixture
def setup(monkeypatch):
    llm = FakeLLM()
    searches = []

    def fake_search(collection, query, k):
        searches.append(query)
        return DOCS

    monkeypatch.setattr(rag_service, "get_llm", lambda: llm)
    monkeypatch.setattr(rag_service, "search_collection", fake_search)
    monkeypatch.setattr(rag_service.settings, "llm_provider", "ollama")
    monkeypatch.setattr(rag_service.settings, "rag_max_distance", None)
    monkeypatch.setattr(rag_service.settings, "rag_rewrite_query", False)
    return llm, searches


def ask(question=QUESTION):
    return asyncio.run(rag_service.answer_question(question))


def chunk(title, path, distance=0.5):
    return (Document(page_content="x", metadata={"title": title, "source": f"x/data/pages/{path}"}), distance)


def test_answer_uses_excerpts_and_original_question(setup):
    llm, searches = setup

    result = ask()

    assert result["answer"].startswith("The answer.")
    assert searches == [QUESTION]  # rewrite is off by default
    system_role, system_text = llm.calls[0][0]
    assert system_role == "system" and "Classpath Scanning" in system_text
    assert "@Component is a stereotype" in system_text
    assert llm.calls[0][1] == ("human", QUESTION)


def test_prompt_tells_the_model_not_to_write_its_own_sources(setup):
    llm, _ = setup

    ask()

    system_text = llm.calls[0][0][1]
    assert "Do not write a list of sources" in system_text


def test_rewrite_adds_spring_terms_to_the_search(setup, monkeypatch):
    llm, searches = setup
    monkeypatch.setattr(rag_service.settings, "rag_rewrite_query", True)

    ask()

    assert searches == [f"{QUESTION} annotation stereotype component"]


def test_rewrite_failure_falls_back_to_the_original_question(setup, monkeypatch):
    llm, searches = setup
    llm.fail_on_rewrite = True
    monkeypatch.setattr(rag_service.settings, "rag_rewrite_query", True)

    result = ask()  # must NOT raise (a missing logger used to turn this into a NameError)

    assert searches == [QUESTION]
    assert result["answer"].startswith("The answer.")


def test_nothing_found_skips_the_model(setup, monkeypatch):
    llm, _ = setup
    monkeypatch.setattr(rag_service, "search_collection", lambda collection, query, k: [])

    result = ask()

    assert result["answer"] == rag_service.NOT_FOUND_MESSAGE
    assert llm.calls == []


def test_answer_is_followed_by_the_retrieved_pages_as_sources(setup, monkeypatch):
    docs = [chunk("Container Overview", "core/beans/basics.adoc"), chunk("Aspect Oriented", "core/aop.adoc", 0.6)]
    monkeypatch.setattr(rag_service, "search_collection", lambda collection, query, k: docs)

    result = ask()

    assert result["answer"] == (
        "The answer.\n\n**Sources**\n"
        "- Container Overview (core/beans/basics.adoc)\n"
        "- Aspect Oriented (core/aop.adoc)"
    )


def test_sources_without_a_path_show_only_the_title(setup):
    result = ask()  # DOCS has a title but no source path

    assert result["answer"] == "The answer.\n\n**Sources**\n- Classpath Scanning"


def test_footer_lists_each_page_once_and_at_most_two(setup, monkeypatch):
    docs = [
        chunk("Beans", "a.adoc", 0.5),
        chunk("Beans", "a.adoc", 0.52),
        chunk("Scopes", "b.adoc", 0.55),
        chunk("AOP", "c.adoc", 0.6),
    ]
    monkeypatch.setattr(rag_service, "search_collection", lambda collection, query, k: docs)

    result = ask()

    assert result["answer"].endswith("**Sources**\n- Beans (a.adoc)\n- Scopes (b.adoc)")


def test_every_retrieved_chunk_is_still_returned_in_sources_field(setup, monkeypatch):
    docs = [chunk("Beans", "a.adoc"), chunk("Scopes", "b.adoc", 0.55), chunk("AOP", "c.adoc", 0.6)]
    monkeypatch.setattr(rag_service, "search_collection", lambda collection, query, k: docs)

    result = ask()

    assert [s["title"] for s in result["sources"]] == ["Beans", "Scopes", "AOP"]
    assert result["retrieved"] == 3


@pytest.mark.parametrize("reply", [
    "I can only help with questions about Spring and its documentation.",
    "The excerpts don't cover this directly, but in general, a pointcut is...",
    "From my general knowledge, a pointcut is...",
])
def test_refusals_and_general_knowledge_answers_get_no_sources(setup, reply):
    llm, _ = setup

    async def says(messages):
        return SimpleNamespace(content=reply)

    llm.ainvoke = says

    assert ask()["answer"] == reply


def test_empty_search_warns_which_collection_was_searched(setup, monkeypatch, caplog):
    monkeypatch.setattr(rag_service, "search_collection", lambda collection, query, k: [])
    monkeypatch.setattr(rag_service.settings, "rag_collection", "spring-docs")

    with caplog.at_level("WARNING"):
        result = ask()

    assert result["answer"] == rag_service.NOT_FOUND_MESSAGE
    assert "spring-docs" in caplog.text and "POST /ingest" in caplog.text


def test_weak_match_skips_the_model_when_a_max_distance_is_set(setup, monkeypatch):
    llm, _ = setup
    monkeypatch.setattr(rag_service.settings, "rag_max_distance", 0.4)  # DOCS best distance is 0.5

    result = ask()

    assert result["answer"] == rag_service.NOT_FOUND_MESSAGE
    assert llm.calls == []


def test_fake_provider_skips_retrieval(monkeypatch):
    llm = FakeLLM()
    monkeypatch.setattr(rag_service, "get_llm", lambda: llm)
    monkeypatch.setattr(rag_service.settings, "llm_provider", "fake")

    def must_not_search(*args):
        raise AssertionError("fake mode must not search")

    monkeypatch.setattr(rag_service, "search_collection", must_not_search)

    result = ask()

    assert result["sources"] == [] and result["retrieved"] == 0