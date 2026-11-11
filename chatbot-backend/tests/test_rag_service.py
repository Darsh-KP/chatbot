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


def test_answer_uses_excerpts_and_original_question(setup):
    llm, searches = setup

    result = ask()

    assert result["answer"] == "The answer."
    assert searches == [QUESTION]  # rewrite is off by default
    system_role, system_text = llm.calls[0][0]
    assert system_role == "system" and "[Excerpt 1: Classpath Scanning" in system_text
    assert llm.calls[0][1] == ("human", QUESTION)


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
    assert result["answer"] == "The answer."


def test_nothing_found_skips_the_model(setup, monkeypatch):
    llm, _ = setup
    monkeypatch.setattr(rag_service, "search_collection", lambda collection, query, k: [])

    result = ask()

    assert result["answer"] == rag_service.NOT_FOUND_MESSAGE
    assert llm.calls == []

def test_empty_search_warns_which_collection_was_searched(setup, monkeypatch, caplog):
    monkeypatch.setattr(rag_service, "search_collection", lambda collection, query, k: [])
    monkeypatch.setattr(rag_service.settings, "rag_collection", "spring-docs")

    with caplog.at_level("WARNING"):
        result = ask()

    assert result["answer"] == rag_service.NOT_FOUND_MESSAGE
    assert "spring-docs" in caplog.text and "POST /ingest" in caplog.text