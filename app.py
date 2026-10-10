import csv
import io
import os
import sqlite3
from contextlib import closing
from datetime import datetime

import matplotlib
from flask import Flask, Response, jsonify, request
from fpdf import FPDF
from werkzeug.security import check_password_hash, generate_password_hash

matplotlib.use("Agg")  # no GUI needed - render charts straight to memory
import matplotlib.pyplot as plt  # noqa: E402

app = Flask(__name__)

VERSION = "3.0"

PROGRAMS = {
    "fat_loss": {
        "name": "Fat Loss (FL)",
        "workout": "Mon: Back Squat 5x5 | Tue: EMOM 20min Assault Bike | "
                   "Wed: Bench Press + 21-15-9 | Thu: Deadlift + Box Jumps | "
                   "Fri: Zone 2 Cardio 30min",
        "diet": "Breakfast: Egg Whites + Oats | Lunch: Grilled Chicken + "
                "Brown Rice | Dinner: Fish Curry + Millet Roti | "
                "Target: ~2000 kcal",
        "calorie_factor": 22,
    },
    "muscle_gain": {
        "name": "Muscle Gain (MG)",
        "workout": "Mon: Squat 5x5 | Tue: Bench 5x5 | Wed: Deadlift 4x6 | "
                   "Thu: Front Squat 4x8 | Fri: Incline Press 4x10 | "
                   "Sat: Barbell Rows 4x10",
        "diet": "Breakfast: Eggs + Peanut Butter Oats | Lunch: Chicken "
                "Biryani | Dinner: Mutton Curry + Rice | Target: ~3200 kcal",
        "calorie_factor": 35,
    },
    "beginner": {
        "name": "Beginner (BG)",
        "workout": "Full Body Circuit: Air Squats, Ring Rows, Push-ups | "
                   "Focus: Technique & Consistency",
        "diet": "Balanced Tamil Meals: Idli / Dosa / Rice + Dal | "
                "Protein Target: 120g/day",
        "calorie_factor": 26,
    },
}

DB_NAME = os.environ.get("ACEEST_DB", "aceest.db")

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def db_execute(sql, params=()):
    with closing(get_db()) as conn:
        conn.execute(sql, params)
        conn.commit()

def db_fetchall(sql, params=()):
    with closing(get_db()) as conn:
        return conn.execute(sql, params).fetchall()

def init_db():
    db_execute("""
        CREATE TABLE IF NOT EXISTS clients (
            name TEXT PRIMARY KEY,
            weight REAL,
            program TEXT,
            calories INTEGER
        )
    """)
    db_execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            week TEXT,
            adherence INTEGER
        )
    """)
    db_execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT
        )
    """)
    if not db_fetchall("SELECT 1 FROM users WHERE username='admin'"):
        db_execute(
            "INSERT INTO users VALUES (?, ?)",
            ("admin", generate_password_hash("admin123")),
        )

init_db()

def calculate_calories(weight, program_id):
    """Daily calorie estimate = weight (kg) x program calorie factor."""
    program = PROGRAMS.get(program_id)
    if program is None:
        return None
    return int(weight * program["calorie_factor"])

@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to ACEest Fitness & Gym API",
        "version": VERSION,
    })

@app.route("/health")
def health():
    return jsonify({"status": "UP"})

@app.route("/programs")
def list_programs():
    return jsonify({key: val["name"] for key, val in PROGRAMS.items()})

@app.route("/programs/<program_id>")
def get_program(program_id):
    program = PROGRAMS.get(program_id)
    if not program:
        return jsonify({"error": "Program not found"}), 404
    return jsonify(program)

@app.route("/client", methods=["POST"])
def create_client():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    weight = data.get("weight")
    program_id = data.get("program")

    if not name or not program_id or weight is None:
        return jsonify({"error": "name, weight and program are required"}), 400
    if not isinstance(weight, (int, float)) or weight <= 0:
        return jsonify({"error": "weight must be a positive number"}), 400

    calories = calculate_calories(weight, program_id)
    if calories is None:
        return jsonify({"error": "Invalid program"}), 404

    program_name = PROGRAMS[program_id]["name"]
    db_execute(
        "INSERT OR REPLACE INTO clients VALUES (?, ?, ?, ?)",
        (name, weight, program_name, calories),
    )
    return jsonify({
        "name": name,
        "weight": weight,
        "program": program_name,
        "estimated_calories": calories,
    })

def row_to_client(row):
    return {
        "name": row["name"],
        "weight": row["weight"],
        "program": row["program"],
        "calories": row["calories"],
    }

@app.route("/client/<name>")
def get_client(name):
    rows = db_fetchall("SELECT * FROM clients WHERE name=?", (name,))
    if not rows:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(row_to_client(rows[0]))

@app.route("/clients")
def list_clients():
    rows = db_fetchall("SELECT * FROM clients ORDER BY name")
    return jsonify([row_to_client(r) for r in rows])

@app.route("/clients/export")
def export_clients():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "weight", "program", "calories"])
    for r in db_fetchall("SELECT * FROM clients ORDER BY name"):
        writer.writerow([r["name"], r["weight"], r["program"], r["calories"]])
    return Response(output.getvalue(), mimetype="text/csv")

@app.route("/progress", methods=["POST"])
def log_progress():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    adherence = data.get("adherence")

    if not name or adherence is None:
        return jsonify({"error": "name and adherence are required"}), 400
    if not isinstance(adherence, int) or not 0 <= adherence <= 100:
        return jsonify({"error": "adherence must be an integer 0-100"}), 400
    if not db_fetchall("SELECT 1 FROM clients WHERE name=?", (name,)):
        return jsonify({"error": "Client not found"}), 404

    week = datetime.now().strftime("Week %U - %Y")
    db_execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
        (name, week, adherence),
    )
    return jsonify({"name": name, "week": week, "adherence": adherence})

@app.route("/client/<name>/progress")
def get_progress(name):
    rows = db_fetchall(
        "SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id",
        (name,),
    )
    return jsonify([{"week": r["week"], "adherence": r["adherence"]} for r in rows])

@app.route("/client/<name>/progress-chart")
def progress_chart(name):
    rows = db_fetchall(
        "SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id",
        (name,),
    )
    if not rows:
        return jsonify({"error": "No progress data for this client"}), 404

    weeks = [r["week"] for r in rows]
    adherence = [r["adherence"] for r in rows]

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(weeks, adherence, marker="o", linewidth=2)
    ax.set_title(f"Weekly Adherence Progress - {name}")
    ax.set_xlabel("Week")
    ax.set_ylabel("Adherence (%)")
    ax.set_ylim(0, 100)
    ax.grid(True)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    return Response(buffer.getvalue(), mimetype="image/png")

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    rows = db_fetchall("SELECT * FROM users WHERE username=?", (username,))
    if rows and check_password_hash(rows[0]["password_hash"], password or ""):
        return jsonify({"message": "Login successful", "username": username})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/client/<name>/report")
def client_report(name):
    rows = db_fetchall("SELECT * FROM clients WHERE name=?", (name,))
    if not rows:
        return jsonify({"error": "Client not found"}), 404
    client = row_to_client(rows[0])

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"ACEest Client Report - {client['name']}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    for label, key in [("Weight (kg)", "weight"), ("Program", "program"),
                       ("Calories (kcal/day)", "calories")]:
        pdf.cell(0, 10, f"{label}: {client[key]}",
                 new_x="LMARGIN", new_y="NEXT")
    return Response(bytes(pdf.output()), mimetype="application/pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)