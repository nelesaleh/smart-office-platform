import random
import datetime
from flask import Blueprint, jsonify, request, send_from_directory

wellness_bp = Blueprint("wellness", __name__)


# ------------------ Wellness Storage ------------------
checkins = []
break_reminders = []

# ------------------ Wellness Routes ------------------
@wellness_bp.route("/api/wellness/checkin", methods=["POST"])
def daily_checkin():
    data = request.json or {}
    user = data.get("user")
    mood = data.get("mood", "neutral")
    energy = data.get("energy", "average")
    if not user:
        return jsonify({"error": "You must provide user"}), 400

    record = {
        "user": user,
        "mood": mood,
        "energy": energy,
        "time": datetime.datetime.now().isoformat()
    }
    checkins.append(record)
    return jsonify({"message": f"Wellness check-in recorded for {user}", "checkin": record})

@wellness_bp.route("/api/wellness/air-quality", methods=["GET"])
def air_quality():
    data = {
        "AQI": random.randint(20, 120),
        "CO2": random.randint(400, 1200),
        "PM2.5": random.randint(5, 50),
        "status": random.choice(["Good", "Moderate", "Unhealthy"])
    }
    return jsonify({"air_quality": data})

@wellness_bp.route("/api/wellness/noise-levels", methods=["GET"])
def noise_levels():
    data = {
        "decibels": random.randint(40, 90),
        "status": random.choice(["Quiet", "Moderate", "Loud"])
    }
    return jsonify({"noise_levels": data})

@wellness_bp.route("/api/wellness/break-reminder", methods=["POST"])
def break_reminder():
    data = request.json or {}
    user = data.get("user")
    minutes = data.get("minutes", 60)
    if not user:
        return jsonify({"error": "You must provide user"}), 400

    reminder = {
        "user": user,
        "minutes": minutes,
        "time_set": datetime.datetime.now().isoformat()
    }
    break_reminders.append(reminder)
    return jsonify({"message": f"Break reminder set for {user} in {minutes} minutes", "reminder": reminder})

@wellness_bp.route("/api/wellness/ergonomics/check", methods=["GET"])
def ergonomics_check():
    tips = [
        "Adjust your chair height so your feet rest flat on the floor.",
        "Keep your monitor at eye level.",
        "Take a 5 minute break every hour.",
        "Sit with your back supported and shoulders relaxed."
    ]
    return jsonify({"ergonomics": random.choice(tips)})

@wellness_bp.route("/api/wellness/mental-health/support", methods=["POST"])
def mental_health_support():
    data = request.json or {}
    user = data.get("user")
    if not user:
        return jsonify({"error": "You must provide user"}), 400

    resources = [
        "Contact HR for confidential counseling services.",
        "Try guided meditation sessions online.",
        "Take short walks to reduce stress.",
        "Reach out to a trusted colleague or friend."
    ]
    return jsonify({"user": user, "resource": random.choice(resources)})

