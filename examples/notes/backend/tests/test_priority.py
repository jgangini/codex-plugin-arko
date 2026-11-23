import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import current_user
from app.features.notes.api import create_router
from app.features.notes.service import Store


@pytest.mark.parametrize("priority", [1, 5])
def test_priority_round_trip(priority: int) -> None:
    app = FastAPI()
    app.include_router(create_router(Store()))
    app.dependency_overrides[current_user] = lambda: "alice"
    with TestClient(app) as client:
        response = client.post("/api/notes", json={"title": "Keep title", "priority": priority})
        assert response.status_code == 201
        item = response.json()
        assert item["priority"] == priority
        assert item["title"] == "Keep title"
        assert client.get(f"/api/notes/{item['id']}").json() == item


@pytest.mark.parametrize("priority", [0, 6, 1.5, "2", True])
def test_priority_rejected(priority: object) -> None:
    app = FastAPI()
    app.include_router(create_router(Store()))
    app.dependency_overrides[current_user] = lambda: "alice"
    with TestClient(app) as client:
        assert client.post("/api/notes", json={"title": "Keep title", "priority": priority}).status_code == 422


def test_existing_request_keeps_default() -> None:
    app = FastAPI()
    app.include_router(create_router(Store()))
    app.dependency_overrides[current_user] = lambda: "alice"
    with TestClient(app) as client:
        response = client.post("/api/notes", json={"title": "Original client"})
        assert response.status_code == 201
        assert response.json()["priority"] == 3
