import pytest

from app import CLIENTS, app, calculate_calories

@pytest.fixture
def client():
    app.config["TESTING"] = True
    CLIENTS.clear()
    with app.test_client() as test_client:
        yield test_client

def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "ACEest" in response.get_json()["message"]

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "UP"

def test_list_programs(client):
    response = client.get("/programs")
    assert response.status_code == 200
    assert "fat_loss" in response.get_json()

def test_get_program_valid(client):
    response = client.get("/programs/fat_loss")
    assert response.status_code == 200
    assert response.get_json()["calorie_factor"] == 22

def test_get_program_invalid(client):
    response = client.get("/programs/invalid")
    assert response.status_code == 404

def test_calculate_calories_logic():
    assert calculate_calories(60, "fat_loss") == 1320
    assert calculate_calories(70, "muscle_gain") == 2450
    assert calculate_calories(50, "unknown") is None

def test_create_client_valid(client):
    response = client.post(
        "/client", json={"name": "Poorva", "weight": 60, "program": "fat_loss"}
    )
    assert response.status_code == 200
    assert response.get_json()["estimated_calories"] == 1320

def test_create_client_missing_fields(client):
    response = client.post("/client", json={"name": "Poorva"})
    assert response.status_code == 400

def test_create_client_invalid_weight(client):
    response = client.post(
        "/client", json={"name": "Poorva", "weight": -5, "program": "fat_loss"}
    )
    assert response.status_code == 400

def test_create_client_invalid_program(client):
    response = client.post(
        "/client", json={"name": "Poorva", "weight": 60, "program": "nope"}
    )
    assert response.status_code == 404

def test_clients_are_stored_and_listed(client):
    client.post("/client", json={"name": "A", "weight": 50, "program": "beginner"})
    client.post("/client", json={"name": "B", "weight": 80, "program": "muscle_gain"})
    response = client.get("/clients")
    assert response.status_code == 200
    assert len(response.get_json()) == 2

def test_export_csv(client):
    client.post("/client", json={"name": "A", "weight": 50, "program": "beginner"})
    response = client.get("/clients/export")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    body = response.get_data(as_text=True)
    assert body.startswith("name,weight,program,calories")
    assert "A,50,Beginner (BG),1300" in body