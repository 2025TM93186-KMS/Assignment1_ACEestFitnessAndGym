import pytest
from app import app

@pytest.fixture
def client():
    """Initializes a sandboxed test client instance for testing routes"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_root(client):
    response = client.get('/api')
    assert response.status_code == 200
    assert response.json['version'] == "2.0.1"

def test_health_check(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == "healthy"

def test_get_programs_list(client):
    """Validates that the program tracking arrays map accurately"""
    response = client.get('/api/programs')
    assert response.status_code == 200
    assert "Fat Loss (FL)" in response.json['programs']

def test_entire_plan_successful_lookup(client):
    response = client.get('/api/entire_plan?program=Muscle Gain (MG)')
    assert response.status_code == 200

def test_missing_parameter_error_gate(client):
    response = client.get('/api/entire_plan')
    assert response.status_code == 400
    assert "Missing required 'program'" in response.json['error']

def test_invalid_plan_not_found_boundary(client):
    response = client.get('/api/entire_plan?program=Zumba')
    assert response.status_code == 404

def test_save_client_success(client):
    payload = {
        "name": "Marcus",
        "program": "Muscle Gain (MG)",
        "age": 30,
        "weight": 85.5
    }
    response = client.post('/api/client', json=payload)
    assert response.status_code == 200
    assert "Client data saved" in response.json["message"]


def test_save_client_validation_missing_fields(client):
    payload = {"name": "", "program": "Fat Loss (FL)"}
    response = client.post('/api/client', json=payload)
    assert response.status_code == 400
    assert "fields are required" in response.json["error"]


def test_load_client_success(client):
    # Seed data
    payload = {"name": "Jane", "program": "Fat Loss (FL)", "age": 28, "weight": 60.0}
    client.post('/api/client', json=payload)

    # Attempt query fetch
    response = client.get('/api/client?name=Jane')
    assert response.status_code == 200
    assert response.json["name"] == "Jane"
    assert response.json["program"] == "Fat Loss (FL)"


def test_load_client_not_found(client):
    response = client.get('/api/client?name=GhostUser')
    assert response.status_code == 404
    assert "not found" in response.json["error"]


def test_save_progress_success(client):
    payload = {
        "name": "Marcus",
        "adherence": 90
    }
    response = client.post('/api/progress', json=payload)
    assert response.status_code == 201
    assert "Weekly progress logged" in response.json["message"]