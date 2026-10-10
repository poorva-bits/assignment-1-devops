from flask import Flask, jsonify, request

app = Flask(__name__)

VERSION = "1.1"

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

    return jsonify({
        "name": name,
        "program": PROGRAMS[program_id]["name"],
        "estimated_calories": calories,
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)