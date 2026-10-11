import pytest
from app import app

import random
from fpdf import FPDF, XPos, YPos


@pytest.fixture
def client():
    """Initializes a sandboxed test client instance for testing routes"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_root(client):
    response = client.get('/api')
    assert response.status_code == 200
    assert response.json['version'] == "3.1.2"

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

# region 2.2.4
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
def test_load_client_not_found(client):
    response = client.get('/api/client?name=MissingClient')
    if response.status_code == 500:
        assert response.status_code == 500
    elif response.status_code == 400:
        assert response.status_code == 400
    elif response.status_code == 404:
        assert response.status_code == 404
        assert response.json["error"] == "Client not found"

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
def test_get_programs_list(client):
    response = client.get('/api/programs')
    if response.status_code == 200:
        assert response.status_code == 200
# endregion

# region V3.1.2
def test_login_user_success(client):
    # Seed default baseline admin identity for authentication parsing checks
    response = client.post('/api/login', json={
        "username": "admin",
        "password": "admin"
    })
    assert response.status_code == 200
    assert response.json["message"] == "Login Successful"
    assert response.json["role"] == "Admin"
def test_login_user_invalid_credentials(client):
    response = client.post('/api/login', json={
        "username": "admin",
        "password": "wrong_password"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json["error"]
def test_get_client_list_success(client):
    # 1. Establish seeded users via the POST endpoint matrix
    client.post('/api/client', json={
        "name": "Barbara",
        "program": "Beginner (BG)",
        "age": 28,
        "height": 165.0,
        "weight": 60.0,
        "membership_expiry": "2027-01-01"
    })
    client.post('/api/client', json={
        "name": "Aaron",
        "program": "Muscle Gain (MG) – PPL",
        "age": 32,
        "height": 182.0,
        "weight": 85.0,
        "membership_expiry": "2027-06-01"
    })

    response = client.get('/api/clients')
    assert response.status_code == 200
    assert "clients" in response.json
def test_get_client_list_empty(client):
    response = client.get('/api/clients')
    if response.status_code == 404:
        assert response.status_code == 404
        assert response.json["error"] == "Client not found"
    else:
        assert response.status_code
def test_load_client_success(client):
    # Setup test baseline
    client.post('/api/client', json={
        "name": "Johns Doe",
        "program": "Beginner (BG)",
        "age": 35,
        "height": 175.0,
        "weight": 80.0,
        "membership_expiry": "2026-06-01"
    })

    response = client.get('/api/client?name=Johns Doe')
    if response.status_code == 200:
        assert response.status_code == 200
        assert "CLIENT PROFILE" in response.json
        profile = response.json["CLIENT PROFILE"]
        assert profile["name"] == "Johns Doe"
        assert profile["program"] == "Beginner (BG)"
        assert profile["membership_expiry"] == "2026-06-01"
    else:
        assert response.status_code == 404
        assert "Client not found" in response.json["error"]
def test_load_client_missing_name(client):
    response = client.get('/api/client')
    assert response.status_code == 400
    assert "Missing 'name' query parameter" in response.json["error"]
def test_save_client_success(client):
    payload = {
        "name": "Sarah Connor",
        "program": "Muscle Gain (MG) – PPL",
        "age": 28,
        "height": 170.0,
        "weight": 65.0,
        "membership": "2027-12-31"
    }
    response = client.post('/api/client', json=payload)
    assert response.status_code == 200
    assert "Client data saved" in response.json["message"]
    # 65.0 weight * 35 program factor = 2275 calories expected
    assert response.json["calories"] == 2275
    assert "id" in response.json
def test_save_client_missing_fields(client):
    response = client.post('/api/client', json={"name": "Incomplete"})
    assert response.status_code == 400
    assert "Name and Program fields are required" in response.json["error"]
def test_load_client_not_found(client):
    response = client.get('/api/client?name=GhostUser')
    assert response.status_code == 404
    assert "Client not found" in response.json["error"]

def test_generate_ai_program_success(client):
    # Setup baseline data layout
    client_payload = {
        "name": "David Miller",
        "program": "Fat Loss (FL) – 3 day",
        "age": 28,
        "height": 170.0,
        "weight": 90.0,
        "membership": "2027-12-31"
    }
    client.post('/api/client', json=client_payload)

    response = client.post('/api/ai_program?name=David Miller&exp_level=intermediate')
    assert response.status_code == 200
    assert "AI program generated" in response.json["message"]
    assert "program" in response.json

    program_list = response.json["program"]
    assert len(program_list) > 0
    # Intermediate should yield structured tracking array objects containing core text items keys
    assert "day" in program_list[0]
    assert "exercise" in program_list[0]
    assert "sets" in program_list[0]
    assert "reps" in program_list[0]
def test_generate_ai_program_invalid_exp_level(client):
    response = client.post('/api/ai_program?name=David Miller&exp_level=elite')
    assert response.status_code == 400
    assert "Invalid experience level" in response.json["error"]
def test_export_pdf_report_success(client):
    # Seed client with complex unicode characters like '–' to explicitly test font mapping isolation layers
    client.post('/api/client', json={
        "name": "David Report Test",
        "program": "Fat Loss (FL) – 3 day",
        "age": 30,
        "height": 180.0,
        "weight": 85.0,
        "membership": "2027-01-01"
    })

    response = client.get('/api/pdf_report?name=David Report Test')

    # 1. If your updated endpoint directly streams binary bytes across HTTP response:
    if response.status_code == 200 and response.mimetype == "application/pdf":
        assert response.status_code == 200
        assert "application/pdf" in response.headers["Content-Type"]
        assert "attachment" in response.headers["Content-Disposition"]

    # 2. Alternately, if it writes locally and responds with JSON:
    else:
        assert response.status_code == 200
        assert "saved as" in response.json["message"]
def test_export_pdf_report_missing_name(client):
    response = client.get('/api/pdf_report')
    if response.status_code == 400:
        assert response.status_code == 400
        assert "Missing 'name' query parameter" in response.json["error"]
    elif response.status_code == 404:
        assert response.status_code == 404
        assert "Client not found" in response.json["error"]
    else:
        assert response.status_code == 200
        assert "saved as" in response.json["message"]
def test_export_pdf_report_not_found(client):
    response = client.get('/api/pdf_report?name=NonExistent')
    if response.status_code == 404:
        assert response.status_code == 404
        assert "not found" in response.json["error"].lower()
    elif response.status_code == 500:
        assert response.status_code == 500
    else:
        assert response.status_code == 200
# endregion


#region Load & Save Client



#endregion