import pytest

from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
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