
import os

os.environ["RESULTS_MODE"] = "demo"

from fastapi.testclient import TestClient
from main import app, verify_firebase_user

app.dependency_overrides[verify_firebase_user] = lambda: "test-user-id"
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rainfall_results_endpoint():
    response = client.get(
        "/api/ai/investigations/test-investigation/results",
        params={"variable": "rainfall"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["variable"] == "rainfall"
    assert data["source"] == "DEMO_DATA"
    assert data["is_demo"] is True
    assert data["p_value"] == 0.03


def test_soil_moisture_not_significant():
    response = client.get(
        "/api/ai/investigations/test-investigation/results",
        params={"variable": "soil moisture"},
    )

    assert response.status_code == 200
    assert response.json()["significant_at_0_05"] is False


def test_unsupported_variable():
    response = client.get(
        "/api/ai/investigations/test-investigation/results",
        params={"variable": "humidity"},
    )

    assert response.status_code == 422


def test_missing_chat_message():
    response = client.post(
        "/api/ai/chat",
        json={"session_id": None},
    )

    assert response.status_code == 422


def test_empty_chat_message():
    response = client.post(
        "/api/ai/chat",
        json={"message": "", "session_id": None},
    )

    assert response.status_code == 422


def test_unknown_session():
    response = client.post(
        "/api/ai/chat",
        json={
            "message": "Hello",
            "session_id": "00000000-0000-0000-0000-000000000000",
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

