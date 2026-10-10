from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS
import sys

import io
import csv

app = Flask(__name__)
CORS(app)  # Eliminates Cross-Origin blocking parameters for client integrations
CLIENTS_DB = []

PROGRAMS = {
            "Fat Loss (FL)": {"workout": "Back Squat, Cardio, Bench, Deadlift, Recovery",
                              "diet": "Egg Whites, Chicken, Fish Curry",
                              "color": "#e74c3c", "calorie_factor": 22},
            "Muscle Gain (MG)": {"workout": "Squat, Bench, Deadlift, Press, Rows",
                                 "diet": "Eggs, Biryani, Mutton Curry",
                                 "color": "#2ecc71", "calorie_factor": 35},
            "Beginner (BG)": {"workout": "Air Squats, Ring Rows, Push-ups",
                              "diet": "Balanced Tamil Meals",
                              "color": "#3498db", "calorie_factor": 26}
        }

# For lowercase mapping
# PROGRAMS_LOWER = {k.lower(): v for k, v in PROGRAMS.items()}

@app.route("/")
def home():
    # This looking for templates/index.html automatically
    return render_template("index.html")

@app.route("/api/v1.1", methods=["GET"])
def api_root_v1_1():
    return jsonify({
        "version": "1.1",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",        
        "available_endpoints": {
            "programs": "GET /api/v1.0/programs",
            "health_v1_0": "GET /api/v1.0/health",
            "entire_plan": "GET /api/v1.0/entire_plan",
            "health": "GET /api/v1.1/health",
            "calculate_calories": "POST /api/v1.1/calculate_calories",
            "save_client": "POST /api/v1.1/save_client"
        }
    }), 200

"""Health Check"""
@app.route("/api/v1.0/health", methods=["GET"])
def health_check_v1_0():
    return jsonify({"status": "healthy", "service": "ACEest Fitness API V1.0 Backend"}), 200

"""Returns a list of all available workout and fitness tracks"""
@app.route("/api/v1.0/programs", methods=["GET"])
def get_programs():
    return jsonify({"programs": list(PROGRAMS.keys())}), 200

"""
    Returns full program details based on the program_name query parameter.
    Example: /api/v1.0/entire_plan?program_name=Fat Loss (FL)
"""
@app.route("/api/v1.0/entire_plan", methods=["GET"])
def get_entire_plan():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing required 'program_name' query parameter"}), 400

    program = PROGRAMS.get(program_name)
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({
        "program_name": program_name,
        "ui_color": program.get("color"),
        "weekly_workout_chart": program.get("workout"),
        "daily_nutrition_plan": program.get("diet")
    }), 200

# ==========================================
# NEW V1.1 ENDPOINTS
# ==========================================
@app.route("/api/v1.1/health", methods=["GET"])
def health_check_v1_1():
    return jsonify({"status": "healthy", "service": "ACEest Fitness API V1.1 Backend"}), 200

@app.route("/api/v1.1/calculate_calories", methods=["POST"])
def calculate_calories():
    data = request.json or {}
    program_name = data.get("program")
    try:
        weight = float(data.get("weight", 0))
    except (ValueError, TypeError):
        weight = 0.0

    if not program_name:
        return jsonify({"calories": "--"})

    program = PROGRAMS.get(program_name)
    if not program or weight <= 0:
        return jsonify({"calories": "--"})

    calories = int(weight * program["calorie_factor"])
    return jsonify({"calories": f"{calories} kcal"})

"""
    Validates profile metrics processing data structures in-memory.
    POST JSON payload: {"name": "Jane", "program": "Muscle Gain (MG)", "age": 25, "weight": 70, "progress": 90}
"""
@app.route("/api/v1.1/save_client", methods=["POST"])
def save_client_v1_1():
    try:
        data = request.json or {}
        name = data.get("name", "").strip()
        program_name = data.get("program")

        if not name or not program_name:
            return jsonify({"error": "Please fill client name and program."}), 400

        program = PROGRAMS.get(program_name)
        if not program:
            return jsonify({"error": f"Program '{program_name}' not found."}), 400

    
        age = int(data.get("age", 0))
        weight = float(data.get("weight", 0))
        target_adherence = int(data.get("progress", 0))
    

        calories = int(weight * program["calorie_factor"]) if weight > 0 else 0

        return jsonify({
            "success": f"Client '{name}' saved successfully.",
            "adherence": target_adherence,
            "calculated_calories": calories
        }), 200
    except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route("/api/v1.1/reset", methods=["GET"])
def reset():
    data = {
        "name": "",
        "age": 0,
        "weight": 0.0,        
        "program": "",
        "adherence": 0,
        "total_calories": "--",
        "weekly_workout_chart": "",
        "daily_nutrition_plan": ""        
    }
    return jsonify(data), 200


# ==========================================
# V1.1.2 ENDPOINTS
# ==========================================

@app.route("/api/v1.1.2/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "ACEest Fitness API V1.1.2 Backend"}), 200

@app.route("/api/v1.1.2", methods=["GET"])
def api_root():
    return jsonify({
        "version": "1.1.2",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",
        "metrics_summary": {
            "capacity_users": 150,
            "area_sq_ft": 10000,
            "break_even_members": 250
        },
        "available_endpoints": {
            "programs": "GET /api/v1.0/programs",
            "health_v1_0": "GET /api/v1.0/health",
            "entire_plan": "GET /api/v1.0/entire_plan",
            "health_v1_1": "GET /api/v1.1/health",
            "calculate_calories": "POST /api/v1.1/calculate_calories",
            "save_client": "POST /api/v1.1/save_client",
            "health": "GET /api/v1.1.2/health",
            "save_client": "POST /api/v1.1.2/save_client",
            "get_clients": "GET /api/v1.1.2/clients",
            "export_csv": "GET /api/v1.1.2/export_csv",
            "clear_clients": "POST /api/v1.1.2/clear_clients"
        }
    }), 200

"""Returns a list of all available workout tracks (v1.1.2 variant)"""
@app.route("/api/v1.1.2/programs", methods=["GET"])
def get_programs_v1_1_2():
    return jsonify({"programs": list(PROGRAMS.keys())}), 200

"""Returns full program details (v1.1.2 variant)"""
@app.route("/api/v1.1.2/entire_plan", methods=["GET"])
def get_entire_plan_v1_1_2():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing required 'program_name' query parameter"}), 400

    program = PROGRAMS.get(program_name)
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({
        "program_name": program_name,
        "ui_color": program.get("color"),
        "weekly_workout_chart": program.get("workout"),
        "daily_nutrition_plan": program.get("diet")
    }), 200

"""Validates and stores client data in-memory"""
@app.route("/api/v1.1.2/save_client", methods=["POST"])
def save_client():
    data = request.json or {}
    name = data.get("name", "").strip()
    program_name = data.get("program")

    if not name or not program_name:
        return jsonify({"error": "Please fill client name and program."}), 400

    program = PROGRAMS.get(program_name)
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found."}), 400

    if any(client['name'].lower() == name.lower() for client in CLIENTS_DB):
        return jsonify({"error": f"A client named '{name}' already exists."}), 400

    try:
        age = int(data.get("age", 0))
        weight = float(data.get("weight", 0))
        target_adherence = int(data.get("progress", 0))
        notes = data.get("notes", "").strip()
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid format for numeric metrics."}), 400

    client_record = {
        "name": name,
        "age": age,
        "weight": weight,
        "program": program_name,
        "adherence": target_adherence,
        "notes": notes
    }

    CLIENTS_DB.append(client_record)
    return jsonify({
        "success": f"Client '{name}' validated and processed successfully.",
        "client_summary": client_record
    }), 200

@app.route("/api/v1.1.2/client", methods=["GET"])
def get_client():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing required 'name' query parameter"}), 400
    client = next((c for c in CLIENTS_DB if c['name'].lower() == name.lower()), None)
    if not client:
        return jsonify({"error": f"Client '{name}' not found."}), 404
    return jsonify({"client": client}), 200

"""Retrieves the array of all stored clients"""
@app.route("/api/v1.1.2/clients", methods=["GET"])
def get_clients():
    return jsonify({"clients": CLIENTS_DB}), 200

"""Dynamically generated CSV text object"""


@app.route("/api/v1.1.2/export_csv", methods=["POST"])
def export_csv():
    name = request.args.get("name")
    client = next((c for c in CLIENTS_DB if c['name'].lower() == name.lower()), None)
    if not CLIENTS_DB or not client:
        #return jsonify({"error": "No clients to export."}), 400
        data = request.json or {}
        if data:
            client = {
                "name": data.get("name"),
                "age": data.get("age"),
                "weight": data.get("weight"),
                "program": data.get("program"),
                "adherence": data.get("adherence"),
                "notes": data.get("notes")
            }

    if not name:
        return jsonify({"error": "Missing required 'name' query parameter"}), 400

    if not client:
        return jsonify({"error": f"Client '{name}' not found."}), 404

    filename = request.args.get("filename") or "aceest_clients.csv"


    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Name", "Age", "Weight", "Program", "Adherence", "Notes"])

    """for client in CLIENTS_DB:
        cw.writerow([
            client["name"], client["age"], client["weight"],
            client["program"], client["adherence"], client["notes"]
        ])"""
    cw.writerow([
        client["name"], client["age"], client["weight"],
        client["program"], client["adherence"], client["notes"]
    ])

    output = si.getvalue()
    return Response(
        output,
        status=200,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


@app.route("/api/v1.1.2/clear_clients", methods=["POST"])
def clear_clients():
    CLIENTS_DB.clear()
    return jsonify({"success": "In-memory database context cleared successfully."}), 200

if __name__ == "__main__":
    port_number = 5000
    for arg in sys.argv:
        if arg.startswith('--port='):
            # FIX: Safely extracts the value after the '=' sign
            port_number = int(arg.split('=')[1])

    print(f"Launching ACEest Fitness Engine on port {port_number}")
    app.run(host='0.0.0.0', port=port_number, debug=False)