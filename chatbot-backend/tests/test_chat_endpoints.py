import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Allow imports from the src directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import main
from repository import chats_repo


def fake_answer_for(question: str) -> str:
    return f"Fake answer to: {question}"


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Use a separate temporary database for every test
    monkeypatch.setattr(chats_repo, "DATABASE_PATH", tmp_path / "test_chat.db")

    # Never call Ollama / the vector store in tests: replace the answer step with a fake.
    async def fake_answer_question(question: str) -> dict:
        return {"answer": fake_answer_for(question), "sources": [], "best_distance": 0.0, "retrieved": 0}

    monkeypatch.setattr(main, "answer_question", fake_answer_question)

    with TestClient(main.app) as test_client:
        yield test_client


def roles_and_texts(messages):
    return [(m["role"], m["message"]) for m in messages]


def test_get_chats_empty(client):
    response = client.get("/chats")

    assert response.status_code == 200
    assert response.json() == {"chats": []}


def test_get_nonexistent_chat(client):
    response = client.get("/chats/999999")

    assert response.status_code == 404


def test_delete_nonexistent_chat(client):
    response = client.delete("/chats/999999")

    assert response.status_code == 404


def test_create_chat(client):
    response = client.post("/chats/new", json={"user_message": "What is FastAPI?"})

    assert response.status_code == 201

    data = response.json()

    assert isinstance(data["chat_id"], int)
    assert data["system_message"] == fake_answer_for("What is FastAPI?")


def test_get_chats_after_creation(client):
    create_response = client.post("/chats/new", json={"user_message": "What is FastAPI?"})

    assert create_response.status_code == 201

    chat_id = create_response.json()["chat_id"]

    response = client.get("/chats")

    assert response.status_code == 200
    assert any(chat["chat_id"] == chat_id for chat in response.json()["chats"])


def test_get_messages_after_creation(client):
    create_response = client.post("/chats/new", json={"user_message": "Hello chatbot"})

    assert create_response.status_code == 201

    chat_id = create_response.json()["chat_id"]

    response = client.get(f"/chats/{chat_id}")

    assert response.status_code == 200

    # The first user message and the system answer are stored together.
    assert roles_and_texts(response.json()["messages"]) == [
        (0, "Hello chatbot"),
        (1, fake_answer_for("Hello chatbot")),
    ]


def test_add_message_to_existing_chat(client):
    create_response = client.post("/chats/new", json={"user_message": "Hello chatbot"})
    assert create_response.status_code == 201

    chat_id = create_response.json()["chat_id"]

    response = client.post(f"/chats/{chat_id}", json={"user_message": "What is FastAPI?"})

    assert response.status_code == 201
    assert response.json() == {"system_message": fake_answer_for("What is FastAPI?")}

    messages_response = client.get(f"/chats/{chat_id}")
    assert messages_response.status_code == 200

    # Alternating user / system messages, oldest first.
    assert roles_and_texts(messages_response.json()["messages"]) == [
        (0, "Hello chatbot"),
        (1, fake_answer_for("Hello chatbot")),
        (0, "What is FastAPI?"),
        (1, fake_answer_for("What is FastAPI?")),
    ]


def test_add_message_to_nonexistent_chat(client):
    response = client.post("/chats/999999", json={"user_message": "Anyone there?"})

    assert response.status_code == 404


def test_delete_existing_chat(client):
    create_response = client.post("/chats/new", json={"user_message": "Chat to delete"})
    assert create_response.status_code == 201

    chat_id = create_response.json()["chat_id"]

    delete_response = client.delete(f"/chats/{chat_id}")

    assert delete_response.status_code == 204

    get_response = client.get(f"/chats/{chat_id}")
    assert get_response.status_code == 404

    chats_response = client.get("/chats")
    assert all(chat["chat_id"] != chat_id for chat in chats_response.json()["chats"])


def test_chat_list_has_no_duplicates(client):
    response = client.post("/chats/new", json={"user_message": "First message"})
    assert response.status_code == 201

    chat_id = response.json()["chat_id"]

    response = client.post(f"/chats/{chat_id}", json={"user_message": "Second message"})
    assert response.status_code == 201

    response = client.get("/chats")
    assert response.status_code == 200

    matching_chats = [chat for chat in response.json()["chats"] if chat["chat_id"] == chat_id]

    assert len(matching_chats) == 1


def test_invalid_message_body(client):
    response = client.post("/chats/new", json={"wrong_field": "Hello"})

    assert response.status_code == 422


def test_blank_message_is_rejected(client):
    assert client.post("/chats/new", json={"user_message": "   "}).status_code == 422

    chat_id = client.post("/chats/new", json={"user_message": "Hi"}).json()["chat_id"]
    assert client.post(f"/chats/{chat_id}", json={"user_message": "   "}).status_code == 422


def test_model_failure_returns_500_and_saves_nothing(client, monkeypatch):
    async def failing_answer_question(question: str) -> dict:
        raise RuntimeError("model is down")

    monkeypatch.setattr(main, "answer_question", failing_answer_question)

    response = client.post("/chats/new", json={"user_message": "Hello"})

    assert response.status_code == 500
    assert response.json() == {"detail": "An unexpected error occurred."}
    # No half-created chat is left behind.
    assert client.get("/chats").json() == {"chats": []}