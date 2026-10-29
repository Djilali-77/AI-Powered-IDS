import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    # Using the context manager runs the lifespan (model loading)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def input_dim(client):
    return client.get("/model-info").json()["input_dim"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_model_info(client):
    body = client.get("/model-info").json()
    assert body["threshold"] > 0
    assert body["input_dim"] > 0


def test_predict_valid_payload(client, input_dim):
    response = client.post("/predict", json={"features": [0.0] * input_dim})
    assert response.status_code == 200
    body = response.json()
    assert body["reconstruction_error"] >= 0
    assert body["label"] in ("normal", "attack")
    assert body["is_attack"] == (body["reconstruction_error"] >= body["threshold"])


def test_predict_wrong_dimension_is_rejected(client):
    response = client.post("/predict", json={"features": [0.0, 1.0, 2.0]})
    assert response.status_code == 422


def test_predict_batch(client, input_dim):
    payload = {"samples": [[0.0] * input_dim, [1.0] * input_dim]}
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.parametrize("kind", ["benign", "attack"])
def test_simulate_returns_ground_truth(client, kind):
    response = client.get(f"/simulate/{kind}")
    if response.status_code == 503:
        pytest.skip("samples.json not generated yet")
    body = response.json()
    assert body["kind"] == kind
    assert isinstance(body["correct"], bool)
    assert body["true_label"]


def test_simulate_invalid_kind(client):
    assert client.get("/simulate/unknown").status_code == 422