from flask import Blueprint, request, jsonify
from .. import mongo
import time
import datetime
from ..utils import parse_time

control_bp = Blueprint("control", __name__, url_prefix="/api/environment")


# --------------------------------------------- LIGHTS API ---------------------------------------------------------
#---------------------------------------------------------------------------------
#POST /api/environment/lights/control - Control office lighting zones
@control_bp.route('/lights/control', methods=['POST'])
def post_control_lights():
    """Controls the state of a single light in the MongoDB 'lights' collection."""
    data = request.json
    mongo.db.lights.update_one(
        {'room': data.get("room")},
        {'$set': {'is_on': bool(data.get("state"))}},
        upsert=True
    )
    return jsonify({"status": "success"})

#-----------------------------------------------------------------------------------------
#GET /api/environment/lights/status - Get current lighting status
@control_bp.route('/lights/status', methods=['GET'])
def get_lights_status():
    lights_cursor = mongo.db.lights.find({})
    status_dict = {light['room']: light['is_on'] for light in lights_cursor}
    return jsonify(status_dict)


# ------------------------------------------ TEMPERATURE + AC API ---------------------------------
#GET /api/environment/temperature/current - Get current temperatures
@control_bp.route('/temperature/current', methods=['GET'])
def get_temperature():
    states_cursor = mongo.db.room_states.find({})
    status_dict = {
        state['room']: {"temperature": state.get('temperature'), "ac_on": state.get('ac_on', False)}
        for state in states_cursor
    }
    return jsonify(status_dict)

#-----------------------------------------------------------------------------------------
#POST /api/environment/temperature/set - Set temperature for zones
@control_bp.route('/temperature/set', methods=['POST'])
def set_temperature():
    """Sets the state of a single AC unit in the 'room_states' collection."""
    data = request.json
    update_doc = {}
    if "ac_on" in data:
        update_doc["ac_on"] = bool(data["ac_on"])
        if not bool(data["ac_on"]):
            update_doc["temperature"] = None
    if "temperature" in data:
        update_doc["temperature"] = data["temperature"]

    mongo.db.room_states.update_one(
        {'room': data.get("room")}, {'$set': update_doc}, upsert=True
    )
    return jsonify({"status": "success"})


#--------------------------------------------------------------------
#POST /api/environment/hvac/schedule - Schedule HVAC operations
@control_bp.route('/hvac/schedule', methods=['POST'])
def set_hvac_schedule():
    """Adds a new HVAC schedule to the 'hvac_schedules' collection."""
    data = request.json
    room = data.get("room")
    start_str = data.get("start")
    end_str = data.get("end")
    temp = data.get("temperature", 22)

    if not room or not start_str or not end_str:
        return jsonify({"error": "room, start, and end are required"}), 400

    start = parse_time(start_str)
    end = parse_time(end_str)
    if not start or not end:
        return jsonify({"error": "Invalid datetime format, use YYYY-MM-DD HH:MM:SS"}), 400
    if end <= start:
        return jsonify({"error": "End time must be after start time"}), 400

    mongo.db.hvac_schedules.insert_one({
        "room": room,
        "start": start_str,
        "end": end_str,
        "temperature": temp,
        "active": False   # ✅ will be activated later by schedule_loop
    })
    return jsonify({"message": f"Schedule added for {room} from {start_str} → {end_str} at {temp}°C"})



def schedule_loop(app):
    """Background task to manage HVAC schedules using MongoDB."""
    while True:
        with app.app_context():
            now = datetime.datetime.now()
            schedules = list(mongo.db.hvac_schedules.find({}))

            for schedule in schedules:
                start_time = parse_time(schedule.get('start'))
                end_time = parse_time(schedule.get('end'))
                room = schedule.get('room')

                if not all([start_time, end_time, room]):
                    continue

                try:
                    if start_time <= now <= end_time:
                        # ACTIVE PERIOD
                        mongo.db.room_states.update_one(
                            {"room": room},
                            {"$set": {"ac_on": True, "temperature": schedule.get("temperature")}},
                            upsert=True
                        )
                        if not schedule.get("active", False):
                            mongo.db.hvac_schedules.update_one(
                                {"_id": schedule["_id"]},
                                {"$set": {"active": True}}
                            )
                            print(f"✅ Schedule started for {room} at {schedule.get('temperature')}°C")

                    elif now > end_time and schedule.get("active", False):
                        # EXPIRED
                        mongo.db.room_states.update_one(
                            {"room": room},
                            {"$set": {"ac_on": False, "temperature": None}}
                        )
                        mongo.db.hvac_schedules.update_one(
                            {"_id": schedule["_id"]},
                            {"$set": {"active": False}}
                        )
                        print(f"⏹ Schedule ended for {room}")
                except Exception as e:
                    print("⚠️ Error in schedule loop:", e)

        time.sleep(5)

