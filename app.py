from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sys
import io
import csv

import sqlite3
from datetime import datetime

import base64
import matplotlib
matplotlib.use('Agg') # Prevents desktop GUI windows from opening
import matplotlib.pyplot as plt

app = Flask(__name__)
CORS(app)  # Eliminates Cross-Origin blocking parameters for client integrations
CLIENTS_DB = []
DB_NAME = "aceest_fitness.db"

PROGRAMS = {
            "Fat Loss (FL)": {"factor": 22},
            "Muscle Gain (MG)": {"factor": 35},
            "Beginner (BG)": {"factor": 26}
}
PROGRAMS_LOWER = {k.lower(): v for k, v in PROGRAMS.items()}

# V2.0.1 :
# ---------- DATABASE LOGIC (ISOLATED LAZY LOADING) ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    age INTEGER,
                    weight REAL,
                    program TEXT,
                    calories INTEGER
                )
    """)

    cur.execute("""
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT,
                    week TEXT,
                    adherence INTEGER
                )
    """)

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("index.html")

def ensure_db_initialized():
    """Checks and builds schemas only when invoked inside v2.0.1 data engines."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                age INTEGER,
                weight REAL,
                program TEXT,
                calories INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                week TEXT,
                adherence INTEGER
            )
        """)
        conn.commit()

@app.route("/api", methods=["GET"])
def api_root():
    return jsonify({
        "version": "2.2.1",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",
        "available_endpoints": {
            "health": "GET /api/health",
            "programs": "GET /api/v1.0/programs",
            "entire_plan": "GET /api/entire_plan",
            "save_client": "POST /api/client",
            "load_client": "GET /api/client",
            "save_progress": "POST /api/progress"
        }
    }), 200

"""Health Check"""
@app.route("/api/health", methods=["GET"])
def health_check():
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "ACEest Fitness API V2.2.1 Backend",
            }
        ),
        200,
    )
#
    #Client and DB Related Operations
#

@app.route("/api/programs", methods=["GET"])
def get_programs():
    return jsonify({"programs": list(PROGRAMS.keys())}), 200

@app.route("/api/entire_plan", methods=["GET"])
def get_entire_plan():
    program_name = request.args.get("program")
    if not program_name:
        return jsonify({"error": "Missing required 'program' query parameter"}), 400

    program = PROGRAMS.get(program_name)
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({
        "program_name": program_name,
        "ui_color": program.get("color"),
        "weekly_workout_chart": program.get("workout"),
        "daily_nutrition_plan": program.get("diet")
    }), 200

@app.route("/api/client", methods=["POST"])
def save_client():
    data = request.json or {}
    name = data.get("name")
    program = data.get("program")

    if not name or not program:
        return jsonify({"error": "Name and Program fields are required"}), 400

    try:
        age = int(data.get("age", 0))
        weight = float(data.get("weight", 0.0))
    except (ValueError, TypeError):
        return (
            jsonify({"error": "Invalid format for age or numerical weight"}),
            400,
        )

    program_details = PROGRAMS_LOWER.get(program.lower())
    if not program_details:
        return jsonify({"error": f"Program '{program}' matches no baseline"}), 404

    calories = int(weight * program_details["factor"])

    program_value = next(
        (key for key, val in PROGRAMS.items() if key.lower() == program.lower()),
        program  # Default string fallback value if no match is found
    )

    try:
        with get_db() as conn:
            client = conn.execute(
                """
                INSERT OR REPLACE INTO clients (name, age, weight, program, calories)
                VALUES (?, ?, ?, ?, ?)
            """,
                (name, age, weight, program_value, calories),
            )
            conn.commit()
        return (
            jsonify({"message": "Client data saved", "id":client.lastrowid, "calories": calories}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/client", methods=["GET"])
def load_client():
    ensure_db_initialized()  # Auto-creates tables seamlessly if missing
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing 'name' query parameter"}), 400

    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM clients WHERE name = ?", (name,)
            ).fetchone()

            if not row:
                return jsonify({"error": "Client not found"}), 404

            return (
                jsonify(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "age": row["age"],
                        "weight": row["weight"],
                        "program": row["program"],
                        "calories": row["calories"],
                    }
                ),
                200,
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/progress", methods=["POST"])
def save_progress():
    data = request.json or {}
    name = data.get("name")

    if not name:
        return jsonify({"error": "Target client 'name' property required"}), 400

    try:
        adherence = int(data.get("adherence", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Adherence configuration must be numerical"}), 400

    week_stamp = datetime.now().strftime("Week %U - %Y")

    try:
        with get_db() as conn:
            progress = conn.execute(
                """
                INSERT INTO progress (client_name, week, adherence)
                VALUES (?, ?, ?)
            """,
                (name, week_stamp, adherence),
            )
            conn.commit()
        return (
            jsonify({"message": "Weekly progress logged", "id": progress.lastrowid}),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# region V2.2.1
@app.route("/api/progress", methods=["GET"])
def load_progress():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing required 'name' filter parameter"}), 400

    try:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, week, adherence 
                FROM progress 
                WHERE client_name = ? 
                ORDER BY id ASC
            """, (name,)).fetchall()

        progress_log = [
            {"id": row["id"], "week": row["week"], "adherence": row["adherence"]}
            for row in rows
        ]
        return jsonify({"client_name": name, "progress": progress_log}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/progress/export", methods=["GET"])
def export_progress():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing required 'name' filter parameter"}), 400

    try:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT week, adherence 
                FROM progress 
                WHERE client_name = ? 
                ORDER BY id ASC
            """, (name,)).fetchall()

        if not rows:
            return jsonify({"error": f"No structural timelines logged for {name}"}), 404

        output = io.StringIO()
        # noinspection PyTypeChecker
        writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)

        # Write CSV Schema Headers
        writer.writerow(["Client Name", "Week Identifier", "Adherence Percentage"])
        for row in rows:
            writer.writerow([name, row["week"], f"{row['adherence']}%"])

        response_stream = output.getvalue()
        output.close()

        # Build streaming response configuration headers
        filename = f"{name.lower().replace(' ', '_')}_progress.csv"
        return Response(
            response_stream,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/progress_chart', methods=['GET'])
def get_progress_chart():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing required 'name' filter parameter"}), 400

    try:
        with get_db() as conn:
            rows = conn.execute("""
                    SELECT id, week, adherence 
                    FROM progress 
                    WHERE client_name = ? 
                    ORDER BY id ASC
                """, (name,)).fetchall()


            for row in rows:
                weeks= row["week"]
                adherence = row["adherence"]


        plt.figure(figsize=(8, 4))
        plt.plot(weeks, adherence, marker="o", linewidth=2)
        plt.title(f"Weekly Adherence Progress – {name}")
        plt.xlabel("Week")
        plt.ylabel("Adherence (%)")
        plt.ylim(0, 100)
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save chart to a memory buffer instead of plt.show()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

        return jsonify({
            "image": f"data:image/png;base64,{image_base64}"
        })
    except Exception as e:
            return jsonify({"error": str(e)}), 500


# endregion



if __name__ == "__main__":
    init_db()
    port_number = 5000
    for arg in sys.argv:
        if arg.startswith('--port='):
            # FIX: Safely extracts the value after the '=' sign
            port_number = int(arg.split('=')[1])

    print(f"Launching ACEest Fitness Engine on port {port_number}")
    app.run(host='0.0.0.0', port=port_number, debug=False)