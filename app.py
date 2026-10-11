from flask import Flask, jsonify, request, render_template, send_file
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

import random
from fpdf import FPDF, XPos, YPos


app = Flask(__name__)
CORS(app)  # Eliminates Cross-Origin blocking parameters for client integrations
CLIENTS_DB = []
DB_NAME = "aceest_fitness.db"

PROGRAMS = {
            "Fat Loss (FL) – 3 day": {"factor": 22, "desc": "3-day full-body fat loss"},
            "Fat Loss (FL) – 5 day": {"factor": 24, "desc": "5-day split, higher volume fat loss"},
            "Muscle Gain (MG) – PPL": {"factor": 35, "desc": "Push/Pull/Legs hypertrophy"},
            "Beginner (BG)": {"factor": 26, "desc": "3-day simple beginner full-body"}
}
PROGRAMS_LOWER = {k.lower(): v for k, v in PROGRAMS.items()}

# V2.0.1 :
# ---------- DATABASE LOGIC (ISOLATED LAZY LOADING) ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        with get_db() as conn:
            cur = conn.cursor()
            # Users table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT
                )
                """
            )
            # Default admin user
            cur.execute(
                "INSERT OR IGNORE INTO users (username, password, role) "
                "VALUES ('admin','admin','Admin')"
            )
            # Clients
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    age INTEGER,
                    height REAL,
                    weight REAL,
                    program TEXT,
                    calories INTEGER,
                    target_weight REAL,
                    target_adherence INTEGER,
                    membership_expiry TEXT
                )
                """
            )
            # Progress
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT,
                    week TEXT,
                    adherence INTEGER
                )
                """
            )
            # Workouts
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT,
                    date TEXT,
                    workout_type TEXT,
                    duration_min INTEGER,
                    notes TEXT
                )
                """
            )
            # Exercises
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workout_id INTEGER,
                    name TEXT,
                    sets INTEGER,
                    reps INTEGER,
                    weight REAL
                )
                """
            )
            # Metrics
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT,
                    date TEXT,
                    weight REAL,
                    waist REAL,
                    bodyfat REAL
                )
                """
            )
            conn.commit()
    finally:
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
        "version": "3.1.2",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",
        "available_endpoints": {
            "health": "GET /api/health",
            "programs": "GET /api/v1.0/programs",
            "entire_plan": "GET /api/entire_plan",
            "save_client": "POST /api/client",
            "load_client": "GET /api/client",
            "save_progress": "POST /api/progress",
            "show_weight_chart": "GET /api/weight",
            "show_bmi_info": "GET /api/bmi",
            "save_workout": "POST /api/workout",
            "save_metrics": "POST /api/metrics",
            "workout_history": "GET /api/workout",
            "get_clients_names": "GET /api/clients/names"
        }
    }), 200
"""Health Check"""
@app.route("/api/health", methods=["GET"])
def health_check():
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "ACEest Fitness API V3.1.2 Backend",
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

# region V2.2.4
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

# region V2.2.4
# ==========================================
# V2.2.4
# ==========================================
@app.route("/api/weight", methods=["GET"])
def show_weight_chart():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing required 'name' filter parameter"}), 400

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT date, weight
                FROM metrics
                WHERE client_name=? AND weight IS NOT NULL
                ORDER BY date
                """,
                (name,),
            )
            data = cur.fetchall()
            if not data:
                return jsonify({"error": "No weight metrics available for this client"}), 404

            return jsonify({"client_name": name, "weight_chart": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bmi", methods=["GET"])
def show_bmi_info():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing required 'name' filter parameter"}), 400

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clients WHERE name=?", (name,))
            client = cur.fetchone()
            if not client:
                return jsonify({"error": "Client not found"}), 404
            height = client["height"]
            weight = client["weight"]

            if height <= 0 or weight <= 0:
                return jsonify({"error", "Missing Data, Enter valid height and weight first"})
            h_m = height / 100.0
            bmi = weight / (h_m * h_m)
            bmi = round(bmi, 1)

            if bmi < 18.5:
                category = "Underweight"
                risk = "Potential nutrient deficiency, low energy."
            elif bmi < 25:
                category = "Normal"
                risk = "Low risk if active and strong."
            elif bmi < 30:
                category = "Overweight"
                risk = "Moderate risk; focus on adherence and progressive activity."
            else:
                category = "Obese"
                risk = "Higher risk; prioritize fat loss, consistency, and supervision."
            return jsonify({"BMI Info":
                    f"BMI for {name}: {bmi} ({category})\n\nRisk note: {risk}"
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/workout", methods=["POST"])
def save_workout():
        try:
            data = request.json or {}
            name = data.get("name")
            workout_type = ["Strength", "Hypertrophy", "Conditioning", "Mixed", "Mobility"]
            w_type = data.get("workout")
            #program = data.get("program")
            if not w_type.lower() in [w.lower() for w in workout_type]:
                return jsonify({"error": "Workout not found"}), 404
            if not name or not w_type:
                return jsonify({"error": "Name and Workout fields are required"}), 400

            date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
            w_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            duration = float(data.get("duration", 0.0))
            notes = data.get("notes", "")

            ex_name = data.get("ex_name", "")
            ex_sets = float(data.get("ex_sets", 0.0))
            ex_reps = float(data.get("ex_reps", 0.0))
            ex_weight = float(data.get("ex_weight", 0.0))

            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, w_date, w_type, duration, notes),
                )
                workout_id = cur.lastrowid

                if ex_name:
                    cur.execute(
                        """
                        INSERT INTO exercises (workout_id, name, sets, reps, weight)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (workout_id, ex_name, ex_sets, ex_reps, ex_weight),
                    )

                conn.commit()
                return (
                    jsonify({"message": "Workout logged successfully", "id": workout_id}),
                    200,
                )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route("/api/metrics", methods=["POST"])
def save_metrics():
        try:
            data = request.json or {}
            name = data.get("name")
            if not name or not data.get("date"):
                return jsonify({"error": "Name and Date fields are required"}), 400

            date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
            m_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            m_weight = float(data.get("weight", 0.0))
            m_waist = float(data.get("waist", 0.0))
            m_bf = float(data.get("body_fat", 0.0))

            with get_db() as conn:
                cur = conn.cursor()
                metrics = cur.execute(
                    """
                    INSERT INTO metrics (client_name, date, weight, waist, bodyfat)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, m_date, m_weight, m_waist, m_bf),
                )
                conn.commit()
            return (
                jsonify({"message": "Metrics logged successfully", "id": metrics.lastrowid}),
                200,
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route("/api/workout", methods=["GET"])
def workout_history():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clients WHERE name=?", (name,))
            client = cur.fetchone()
            if not client:
                return jsonify({"error": "Client not found"}), 404
            # ------------------
            cur.execute(
                """
                SELECT date, workout_type, duration_min, notes
                FROM workouts
                WHERE client_name=?
                ORDER BY date DESC, id DESC
                """,
                (name,),
            )
            workouts = cur.fetchall()
            serializable_workouts = [tuple(row) for row in workouts]
            return (
                jsonify({"workout_history": serializable_workouts}),
                200,
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# endregion

@app.route("/api/clients/names", methods=["GET"])
def get_clients_names():
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM clients ORDER BY name ASC")
            rows = cur.fetchall()
            if not rows:
                return jsonify({"error": "Clients not found"}), 404

            names = [row["name"] for row in rows]

            return jsonify({
                "clients": names
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# endregion

# region V3.1.2
@app.route("/api/login", methods=["POST"])
def login_user():
    try:
        data = request.json or {}
        username = data.get("username")
        password = data.get("password")

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT role FROM users WHERE username=? AND password=?",
                (username, password),
            )
            user = cur.fetchone()
            if user:
                return jsonify({"message": "Login Successful", "role": user["role"]}), 200
            else:
                return jsonify({"error": "Invalid credentials\nTry admin / admin"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/clients", methods=["GET"])
def get_client_list():
    try:

        with get_db() as conn:
            cur = conn.cursor()
            client = cur.execute("SELECT * FROM clients ORDER BY name")
            rows = cur.fetchall()
            if not client:
                return jsonify({"error": "Client not found"}), 404
            client_list = []
            for client in rows:
                client_list.append({
                    "id": client["id"],
                    "name": client["name"],
                    "age": client["age"],
                    "height": client["height"],
                    "weight": client["weight"],
                    "program": client["program"],
                    "calories": client["calories"],
                    "membership_expiry": client["membership_expiry"]
                })
            return jsonify({"clients": client_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/client", methods=["POST"])
def save_client():
        try:
            data = request.json or {}
            name = data.get("name")
            program = data.get("program")
            if not name or not program:
                return jsonify({"error": "Name and Program fields are required"}), 400

            age = int(data.get("age", 0))
            height = float(data.get("height", 0.0))
            weight = float(data.get("weight", 0.0))
            membership = data.get("membership_expiry")
            program_details = PROGRAMS_LOWER.get(program.lower())
            if not program_details:
                return jsonify({"error": f"Program '{program}' matches no baseline"}), 404
            factor = float(program_details["factor"])
            calories = int(weight * factor) if weight > 0 else None
            program_value = next(
                (key for key, val in PROGRAMS.items() if key.lower() == program.lower()),
                program  # Default string fallback value if no match is found
            )


            with get_db() as conn:
                cur = conn.cursor()
                client = cur.execute(
                    """
                    INSERT OR REPLACE INTO clients
                    (name, age, height, weight, program, calories, membership_expiry)
                    VALUES (?,?,?,?,?,?,?)
                    """,
                    (name, age, height, weight, program, calories, membership),
                )
                conn.commit()
                return (
                    jsonify({"message": "Client data saved", "id": client.lastrowid, "calories": calories}),
                    200,
                )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
@app.route("/api/client", methods=["GET"])
def load_client():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clients WHERE name=?", (name,))
            client = cur.fetchone()
            if not client:
                return jsonify({"error": "Client not found"}), 404
            client_profile = {
                "id": client["id"],
                "name": client["name"],
                "age": client["age"],
                "height": client["height"],
                "weight": client["weight"],
                "program": client["program"],
                "calories": client["calories"],
                "membership_expiry": client["membership_expiry"]
            }
            return jsonify({"CLIENT PROFILE": client_profile}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/ai_program", methods=["POST"])
def generate_ai_program():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400
        exp_level = request.args.get("exp_level")
        if not exp_level or exp_level.lower() not in ["beginner", "intermediate", "advanced"]:
            return jsonify({"error": "Invalid experience level"}), 400

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT program FROM clients WHERE name=?", (name,))
            client = cur.fetchone()
            if not client:
                return jsonify({"error": "Client not found"}), 404
            program_name = client[0]
            exercises_pool = {
                "Strength": [
                    "Squat",
                    "Deadlift",
                    "Bench Press",
                    "Overhead Press",
                    "Pull-Up",
                    "Barbell Row",
                ],
                "Hypertrophy": [
                    "Leg Press",
                    "Incline Dumbbell Press",
                    "Lat Pulldown",
                    "Lateral Raise",
                    "Bicep Curl",
                    "Tricep Extension",
                ],
                "Conditioning": [
                    "Running",
                    "Cycling",
                    "Rowing",
                    "Burpees",
                    "Jump Rope",
                    "Kettlebell Swings",
                ],
                "Full Body": [
                    "Push-Up",
                    "Pull-Up",
                    "Lunge",
                    "Plank",
                    "Dumbbell Row",
                    "Dumbbell Press",
                ],
            }
            focus = "Full Body"
            if "Fat Loss" in program_name:
                focus = "Conditioning"
            elif "Muscle Gain" in program_name:
                focus = "Hypertrophy"

            if exp_level.lower() == "beginner":
                sets_range = (2, 3)
                reps_range = (8, 12)
                days = 3
            elif exp_level.lower() == "intermediate":
                sets_range = (3, 4)
                reps_range = (8, 15)
                days = 4
            else:
                sets_range = (4, 5)
                reps_range = (6, 15)
                days = 5

            weekly_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][:days]
            program_tree = []

            for day in weekly_days:
                exercises = random.sample(exercises_pool[focus], k=3 if days < 4 else 4)
                for ex in exercises:
                    sets = random.randint(*sets_range)
                    reps = random.randint(*reps_range)
                    program_tree.append({"day": day, "exercise": ex, "sets": sets, "reps": reps})

            return jsonify({
                "message": f"AI program generated for {name}",
                "program": program_tree
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/pdf_report", methods=["GET"])
def export_pdf_report():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400
        pdf = FPDF()
        pdf.add_page()

        # Title Block - Clean and warn-free
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"Client Report - {name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font("Helvetica", "", 12)

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clients WHERE name=?", (name,))
            row = cur.fetchone()
            if row:
                pdf.ln(10)

                program_text = str(row["program"] or "").replace('–', '-')
                expiry_text = str(row["membership_expiry"] or "").replace('–', '-')

                # FIX: Replaced invalid string values with proper XPos and YPos Enums
                pdf.cell(0, 10, f"Name: {row['name']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 10, f"Age: {row['age']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 10, f"Height: {row['height']} cm", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 10, f"Weight: {row['weight']} kg", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 10, f"Program: {program_text}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.cell(0, 10, f"Membership Expiry: {expiry_text}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # pdf.output(f"{name}_report.pdf")
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        return send_file(
            pdf_output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{name}_report.pdf"
        )
        # return jsonify({"message": f"Report saved as {name}_report.pdf"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# endregion


init_db()
if __name__ == "__main__":
    port_number = 5000
    for arg in sys.argv:
        if arg.startswith('--port='):
            # FIX: Safely extracts the value after the '=' sign
            port_number = int(arg.split('=')[1])

    print(f"Launching ACEest Fitness Engine on port {port_number}")
    app.run(host='0.0.0.0', port=port_number, debug=False)