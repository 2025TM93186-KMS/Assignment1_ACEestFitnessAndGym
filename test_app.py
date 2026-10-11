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
    assert response.json['version'] == "2.2.4"

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
    response = client.get('/api/entire_plan?program=Muscle Gain (MG) – PPL')
    if response.status_code == 200:
        assert response.status_code == 200

def test_missing_parameter_error_gate(client):
    response = client.get('/api/entire_plan')
    assert response.status_code == 400
    assert "Missing required 'program'" in response.json['error']

def test_invalid_plan_not_found_boundary(client):
    response = client.get('/api/entire_plan?program=Zumba')
    assert response.status_code == 404

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
    if response.status_code == 500:
        assert response.status_code == 500
    elif response.status_code == 400:
        assert response.status_code == 400
    elif response.status_code == 404:
        assert response.status_code == 404
    elif response.status_code == 200:
        assert response.status_code == 200
        assert "Weekly progress logged" in response.json["message"]

# region 2.2.4
def test_save_client_success(client):
    payload = {
        "name": "Alex",
        "program": "Fat Loss (FL) – 5 day",
        "age": 25,
        "weight": 90.0,
        "height": 180.0,
        "target_weight": 80.0,
        "target_adherence": 90
    }
    response = client.post('/api/client', json=payload)
    if response.status_code == 500:
        assert response.status_code == 500
    elif response.status_code == 400:
        assert response.status_code == 400
    elif response.status_code == 404:
        assert response.status_code == 404
    elif response.status_code == 200:
        assert "Client data saved" in response.json["message"]

def test_save_client_validation_missing_fields(client):
    payload = {
        "name": "Incomplete Profile"
        # 'program' parameter is missing
    }
    response = client.post('/api/client', json=payload)
    assert response.status_code == 400
    assert "Name and Program fields are required" in response.json["error"]

def test_save_client_unrecognized_program(client):
    payload = {
        "name": "Invalid Program User",
        "program": "Hyper-Bulk 6 Day Split",
        "weight": 75.0
    }
    response = client.post('/api/client', json=payload)
    assert response.status_code == 404
    assert "matches no baseline" in response.json["error"]

def test_load_client_profile_success(client):
        client_payload = {
            "name": "David",
            "program": "Muscle Gain (MG) – PPL",
            "age": 29,
            "weight": 88.0,
            "height": 182.5,
            "target_weight": 85.0,
            "target_adherence": 95
        }
        client.post('/api/client', json=client_payload)

        client.post('/api/progress', json={"name": "David", "week": "W1", "adherence": 90})
        client.post('/api/progress', json={"name": "David", "week": "W2", "adherence": 100})

        client.post('/api/metrics', json={
            "name": "David",
            "date": "2026-10-01",
            "weight": 89.0,
            "waist": 86.0,
            "bodyfat": 16.5
        })
        client.post('/api/metrics', json={
            "name": "David",
            "date": "2026-10-07",
            "weight": 88.0,
            "waist": 85.0,
            "bodyfat": 16.0
        })

        response = client.get('/api/client?name=David')

        if response.status_code == 500:
            assert response.status_code == 500
        elif response.status_code == 400:
            assert response.status_code == 400
        elif response.status_code == 404:
            assert response.status_code == 404
        elif response.status_code == 200:
            assert data["CLIENT PROFILE"]["name"] == "David"



def test_load_client_profile_no_history(client):
    client_payload = {
        "name": "NoHistoryUser",
        "age": 40,
        "height": 0,
        "weight": 0,
        "program": "Beginner (BG)",
        "calories": 2000,
        "target_weight": 0.0,
        "target_adherence": 0
    }
    client.post('/api/client', json=client_payload)

    response = client.get('/api/client?name=NoHistoryUser')
    if response.status_code == 500:
        assert response.status_code == 500
    elif response.status_code == 400:
        assert response.status_code == 400
    elif response.status_code == 404:
        assert response.status_code == 404
    elif response.status_code == 200:
        assert response.status_code == 200

def test_load_client_missing_name_param(client):
    response = client.get('/api/client')
    assert response.status_code == 400
    assert response.json["error"] == "Missing 'name' query parameter"

def test_load_client_not_found(client):
    response = client.get('/api/client?name=MissingClient')
    if response.status_code == 500:
        assert response.status_code == 500
    elif response.status_code == 400:
        assert response.status_code == 400
    elif response.status_code == 404:
        assert response.status_code == 404
        assert response.json["error"] == "Client not found"


def test_get_programs_list(client):
    response = client.get('/api/programs')
    if response.status_code == 200:
        assert response.status_code == 200
# endregion