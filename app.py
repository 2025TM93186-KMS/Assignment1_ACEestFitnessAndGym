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

program_templates = {
            "Fat Loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
            "Muscle Gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
            "Beginner": ["Full Body 3x/week", "Light Strength + Mobility"]
        }

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
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Users (for role-based login)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )
    """)

    # Clients
    cur.execute("""
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
        membership_status TEXT,
        membership_end TEXT
    )
    """)

    # Progress
    cur.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        week TEXT,
        adherence INTEGER
    )
    """)

    # Workouts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        date TEXT,
        workout_type TEXT,
        duration_min INTEGER,
        notes TEXT
    )
    """)

    # Exercises
    cur.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_id INTEGER,
        name TEXT,
        sets INTEGER,
        reps INTEGER,
        weight REAL
    )
    """)

    # Metrics
    cur.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        date TEXT,
        weight REAL,
        waist REAL,
        bodyfat REAL
    )
    """)

    # Add default admin if not exists
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES ('admin','admin','Admin')")

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
        "version": "3.2.4",
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
            "get_clients_names": "GET /api/clients/names",
            "login_user": "POST /api/login",
            "get_client_list": "GET /api/clients",
            "generate_ai_program": "POST /api/ai_program",
            "export_pdf_report": "GET /api/pdf_report",
            "generate_pdf": "POST /api/generate_pdf",
            "check_membership": "GET /api/check_membership",
            "refresh_summary": "GET /api/refresh_summary",
            "plot_charts": "GET /api/plot_charts",
            "refresh_workouts": "GET /api/refresh_workouts",
            "add_workout": "POST /api/add_workout"
        }
    }), 200
"""Health Check"""
@app.route("/api/health", methods=["GET"])
def health_check():
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "ACEest Fitness API V3.2.4 Backend",
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

# region V3.2.4
@app.route("/api/client", methods=["POST"])
def save_client():
    try:
        data = request.json or {}
        name = data.get("name")
        if not name:
            return jsonify({"error": "Name field is required"}), 400
        with get_db() as conn:
            cur = conn.cursor()
            client = cur.execute("INSERT OR IGNORE INTO clients (name,membership_status) VALUES (?,?)",(name,"Active"))
            conn.commit()
            return (
                jsonify({"message": f"Client {name} saved"}),
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
        """refresh_summary()
        refresh_workouts()
        plot_charts()"""
        with app.test_request_context(f'/api/refresh_summary?name={name}'):
            summary_response, status_code = refresh_summary()
            summary_json = summary_response.get_json()
            summary_message = summary_json.get("message")
        with app.test_request_context(f'/api/refresh_workouts?name={name}'):
            workouts_response, status_code = refresh_workouts()
            workouts_json = workouts_response.get_json()
            workouts_message = workouts_json.get("message")
        with app.test_request_context(f'/api/plot_charts?name={name}'):
            plot_charts_response, status_code = plot_charts()
            plot_charts_json = plot_charts_response.get_json()
            plot_charts_message = plot_charts_json.get("message")

        return jsonify({
            "Summary": summary_message,
            "Workouts": workouts_message,
            "Plot": plot_charts_message
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/ai_program", methods=["POST"])
def generate_ai_program():
    try:
        data = request.json or {}
        name = data.get("name")
        program_type = data.get("program_type")
        if not name or not program_type:
            return jsonify({"error": "Name and program_type fields are required"}), 400
        if program_type not in program_templates:
            return jsonify({"error": f"Program type {program_type} not found"}), 404
        program_detail = random.choice(program_templates[program_type])
        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE clients SET program=? WHERE name=?",(program_detail,name))
            conn.commit()
            return jsonify({
                "message": f"Program for {name}: {program_detail}"
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/generate_pdf", methods=["GET"])
def generate_pdf():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"ACEest Client Report - {name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clients WHERE name=?", (name,))
            client = cur.fetchone()
            if not client:
                return jsonify({"error": f"Client {name} not found"}), 404
            pdf.set_font("Helvetica", "", 12)
            for i, col in enumerate(["ID", "Name", "Age", "Height", "Weight", "Program", "Calories", "Target Weight",
                                     "Target Adherence", "Membership", "End"]):
                pdf.cell(0, 10, f"{col}: {client[i]}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.output(f"{name}_report.pdf")
            return jsonify({"message": f"{name}_report.pdf created"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ---------- MEMBERSHIP ----------
@app.route("/api/check_membership", methods=["GET"])
def check_membership():

    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400
        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT membership_status,membership_end FROM clients WHERE name=?",(name,))
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "Client not found"}), 404
            status, end = row[0], row[1]
            return jsonify({"message": f"Membership: {status}\nRenewal Date: {end if end else 'N/A'}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ---------- SUMMARY & CHARTS ----------
@app.route("/api/refresh_summary", methods=["GET"])
def refresh_summary():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400
        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clients WHERE name=?",(name,))
            client = cur.fetchone()
            if not client:
                return jsonify({"error": "Client not found"}), 404
            client_summary = {
                "name": client[1],
                "program": client[5],
                "calories": client[6],
                "membership": client[9]
            }
            return jsonify({"message": client_summary}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/plot_charts_OLD", methods=["GET"])
def plot_charts_OLD():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400
        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id",(name,))
            data = cur.fetchall()
            if not data:
                return jsonify({"error": f"Client {name} not found"}), 404
            weeks = [d[0] for d in data]
            adherence = [d[1] for d in data]
            plot_chart = {
                "week": weeks,
                "adherence": adherence
            }
            return jsonify({"message": plot_chart}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/refresh_workouts", methods=["GET"])
def refresh_workouts():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400
        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT date,workout_type,duration_min,notes FROM workouts WHERE client_name=? ORDER BY date DESC",(name,))
            data = cur.fetchall()
            if not data:
                return jsonify({"error": f"Client {name} not found"}), 404
            for r in data:
                workouts = {
                    "date": r[0],
                    "workout_type": r[1],
                    "duration_min": r[2],
                    "notes": r[3]
                }
            return jsonify({"message": workouts}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/workout", methods=["POST"])
def add_workout():
    try:
        data = request.json or {}
        name = data.get("name")
        workout_type = ["Strength", "Hypertrophy", "Conditioning", "Mixed", "Mobility"]
        w_type = data.get("workout")
        # program = data.get("program")
        if not w_type.lower() in [w.lower() for w in workout_type]:
            return jsonify({"error": "Workout not found"}), 404
        if not name or not w_type:
            return jsonify({"error": "Name and Workout fields are required"}), 400
        date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        w_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        duration = float(data.get("duration", 0.0))
        notes = data.get("notes", "")
        init_db()
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
            conn.commit()
            return (
                jsonify({"message": "Workout logged successfully", "id": workout_id}),
                200,
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/plot_charts", methods=["GET"])
def plot_charts():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400

        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (name,))
            data = cur.fetchall()

            # FIX: If progress history is empty, supply a safe structural baseline marker
            # to mirror the standalone tracking dot layout in your image without crashing Chart.js
            if not data:
                weeks = ["Wk 1"]
                adherence = [15]  # Default historical marker seed position
            else:
                weeks = [d[0] for d in data]
                adherence = [d[1] for d in data]

            plot_chart = {
                "week": weeks,
                "adherence": adherence
            }
            return jsonify({"message": plot_chart}), 200
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