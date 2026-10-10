import pytest

from app import app, calculate_calories, db_execute


@pytest.fixture
def client():
    app.config["TESTING"] = True
    db_execute("DELETE FROM clients")
    db_execute("DELETE FROM progress")
    with app.test_client() as test_client:
        yield test_client


def add_client(client, name="A", weight=50, program="beginner"):
    return client.post(
        "/client", json={"name": name, "weight": weight, "program": program}
    )


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "ACEest" in response.get_json()["message"]


def test_health(client):
    assert client.get("/health").get_json()["status"] == "UP"


def test_list_programs(client):
    response = client.get("/programs")
    assert response.status_code == 200
    assert "fat_loss" in response.get_json()


def test_get_program_valid(client):
    response = client.get("/programs/fat_loss")
    assert response.status_code == 200
    assert response.get_json()["calorie_factor"] == 22


def test_get_program_invalid(client):
    assert client.get("/programs/invalid").status_code == 404


def test_calculate_calories_logic():
    assert calculate_calories(60, "fat_loss") == 1320
    assert calculate_calories(70, "muscle_gain") == 2450
    assert calculate_calories(50, "unknown") is None


def test_create_client_valid(client):
    response = add_client(client, "Poorva", 60, "fat_loss")
    assert response.status_code == 200
    assert response.get_json()["estimated_calories"] == 1320


def test_create_client_missing_fields(client):
    assert client.post("/client", json={"name": "Poorva"}).status_code == 400


def test_create_client_invalid_weight(client):
    assert add_client(client, "P", -5, "fat_loss").status_code == 400


def test_create_client_invalid_program(client):
    assert add_client(client, "P", 60, "nope").status_code == 404


def test_client_is_persisted_and_loadable(client):
    add_client(client, "DBTest", 70, "muscle_gain")
    response = client.get("/client/DBTest")
    assert response.status_code == 200
    assert response.get_json()["calories"] == 2450


def test_get_unknown_client(client):
    assert client.get("/client/ghost").status_code == 404


def test_clients_listed(client):
    add_client(client, "A")
    add_client(client, "B", 80, "muscle_gain")
    response = client.get("/clients")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_export_csv(client):
    add_client(client, "A")
    response = client.get("/clients/export")
    assert response.mimetype == "text/csv"
    body = response.get_data(as_text=True)
    assert body.startswith("name,weight,program,calories")
    assert "A,50.0,Beginner (BG),1300" in body


def test_log_progress(client):
    add_client(client, "A")
    response = client.post("/progress", json={"name": "A", "adherence": 85})
    assert response.status_code == 200
    assert response.get_json()["adherence"] == 85


def test_log_progress_unknown_client(client):
    response = client.post(
        "/progress", json={"name": "ghost", "adherence": 50})
    assert response.status_code == 404


def test_log_progress_invalid_value(client):
    add_client(client, "A")
    response = client.post("/progress", json={"name": "A", "adherence": 150})
    assert response.status_code == 400


def test_progress_history(client):
    add_client(client, "A")
    client.post("/progress", json={"name": "A", "adherence": 70})
    client.post("/progress", json={"name": "A", "adherence": 90})
    response = client.get("/client/A/progress")
    assert response.status_code == 200
    assert [p["adherence"] for p in response.get_json()] == [70, 90]


def test_progress_chart_returns_png(client):
    add_client(client, "A")
    client.post("/progress", json={"name": "A", "adherence": 70})
    response = client.get("/client/A/progress-chart")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data.startswith(b"\x89PNG")


def test_progress_chart_without_data(client):
    add_client(client, "A")
    assert client.get("/client/A/progress-chart").status_code == 404


def test_login_success(client):
    response = client.post(
        "/login", json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    assert response.get_json()["username"] == "admin"


def test_login_wrong_password(client):
    response = client.post(
        "/login", json={"username": "admin", "password": "wrong"}
    )
    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post("/login", json={"username": "x", "password": "y"})
    assert response.status_code == 401


def test_client_report_pdf(client):
    add_client(client, "A")
    response = client.get("/client/A/report")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_client_report_unknown_client(client):
    assert client.get("/client/ghost/report").status_code == 404
