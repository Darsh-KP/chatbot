
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Allow imports from the src directory
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

from main import app
from repository import chats_repo


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Use a separate temporary database for every test
    db_path = tmp_path / "test_chat.db"

    monkeypatch.setattr(
        chats_repo,
        "DATABASE_PATH",
        db_path
    )

    with TestClient(app) as test_client:
        yield test_client


def test_get_chats_empty(client):
    response = client.get("/chats")

    assert response.status_code == 200
    assert response.json() == []


def test_get_nonexistent_chat(client):
    response = client.get("/chats/999999")

    assert response.status_code == 404


def test_delete_nonexistent_chat(client):
    response = client.delete("/chats/999999")

    assert response.status_code == 404


def test_create_chat(client):
    response = client.post(
        "/chats/new",
        json={"user_message": "What is FastAPI?"}
    )

    assert response.status_code == 201

    data = response.json()

    assert "chat_id" in data
    assert isinstance(data["chat_id"], int)
    assert data["system_message"] is None


def test_get_chats_after_creation(client):
    create_response = client.post(
        "/chats/new",
        json={"user_message": "What is FastAPI?"}
    )

    assert create_response.status_code == 201

    chat_id = create_response.json()["chat_id"]

    response = client.get("/chats")

    assert response.status_code == 200

    chats = response.json()

    assert any(
        chat["chat_id"] == chat_id
        for chat in chats
    )


def test_get_messages_after_creation(client):
    create_response = client.post(
        "/chats/new",
        json={"user_message": "Hello chatbot"}
    )

    assert create_response.status_code == 201

    chat_id = create_response.json()["chat_id"]

    response = client.get(f"/chats/{chat_id}")

    assert response.status_code == 200

    messages = response.json()

    assert len(messages) >= 1
    assert messages[0]["text"] == "Hello chatbot"
    assert messages[0]["role"] == 0


def test_add_message_to_existing_chat(client):
    create_response = client.post(
        "/chats/new",
        json={"user_message": "Hello chatbot"}
    )
    assert create_response.status_code == 201

    chat_id = create_response.json()["chat_id"]

    response = client.post(
        f"/chats/{chat_id}",
        json={
            "role": 0,
            "text": "What is FastAPI?"
        }
    )

    assert response.status_code == 201

    messages_response = client.get(f"/chats/{chat_id}")
    assert messages_response.status_code == 200

    messages = messages_response.json()

    assert len(messages) == 2
    assert messages[0]["text"] == "Hello chatbot"
    assert messages[1]["text"] == "What is FastAPI?"


def test_delete_existing_chat(client):
    create_response = client.post(
        "/chats/new",
        json={"user_message": "Chat to delete"}
    )
    assert create_response.status_code == 201

    chat_id = create_response.json()["chat_id"]

    delete_response = client.delete(f"/chats/{chat_id}")

    assert delete_response.status_code == 204

    get_response = client.get(f"/chats/{chat_id}")
    assert get_response.status_code == 404

    chats_response = client.get("/chats")
    assert all(
        chat["chat_id"] != chat_id
        for chat in chats_response.json()
    )


def test_chat_list_has_no_duplicates(client):
    response = client.post(
        "/chats/new",
        json={"user_message": "First message"}
    )
    assert response.status_code == 201

    chat_id = response.json()["chat_id"]

    response = client.post(
        f"/chats/{chat_id}",
        json={"role": 0, "text": "Second message"}
    )
    assert response.status_code == 201

    response = client.get("/chats")
    assert response.status_code == 200

    matching_chats = [
        chat for chat in response.json()
        if chat["chat_id"] == chat_id
    ]

    assert len(matching_chats) == 1


def test_invalid_message_body(client):
    response = client.post(
        "/chats/new",
        json={"wrong_field": "Hello"}
    )

    assert response.status_code == 422
