# App/blueprints/meeting_rooms.py
from flask import Blueprint, request, jsonify
from .. import mongo
import datetime
import pytz

meeting_bp = Blueprint("meeting_rooms", __name__, url_prefix="/api/meetings")


def seed_meeting_rooms():
    """Creates the initial meeting room documents if they don't exist."""
    if mongo.db.meeting_rooms.count_documents({}) == 0:
        print("Seeding meeting rooms...")
        rooms_to_seed = [
            {
                "room_name": "london", "is_available": True, "has_projector": True, "has_tv": True,
                "projector_on": False, "tv_on": False, "booked_until": None, "booking_id": None
            },
            {
                "room_name": "boot", "is_available": True, "has_projector": False, "has_tv": True,
                "projector_on": False, "tv_on": False, "booked_until": None, "booking_id": None
            },
            {
                "room_name": "meeting", "is_available": True, "has_projector": True, "has_tv": False,
                "projector_on": False, "tv_on": False, "booked_until": None, "booking_id": None
            }
        ]
        mongo.db.meeting_rooms.insert_many(rooms_to_seed)
        print("Meeting rooms seeded.")


# --- API ROUTES ---

@meeting_bp.route('/rooms/available', methods=['GET'])
def get_available_rooms():
    """Return only rooms that are marked as available."""
    available_rooms_cursor = mongo.db.meeting_rooms.find({"is_available": True})
    available = [room['room_name'] for room in available_rooms_cursor]
    return jsonify({"available_rooms": available})


@meeting_bp.route('/rooms/book', methods=['POST'])
def book_room():
    data = request.json
    room_name = data.get("room")

    room = mongo.db.meeting_rooms.find_one({"room_name": room_name})
    if not room:
        return jsonify({"error": "Invalid room"}), 400
    if not room.get('is_available', True):
        return jsonify({"error": "Room already booked"}), 409

    # Use your local timezone for correct timestamps
    local_tz = pytz.timezone('Asia/Jerusalem')
    now_local = datetime.datetime.now(local_tz)
    end_time = now_local + datetime.timedelta(hours=1)
    booking_id = f"bk-{int(datetime.datetime.utcnow().timestamp())}"

    mongo.db.meeting_rooms.update_one(
        {"room_name": room_name},
        {"$set": {
            "is_available": False,
            "booked_until": end_time.isoformat(),  # Always save as ISO string
            "booking_id": booking_id
        }}
    )
    return jsonify({"message": f"{room_name} booked until {end_time.isoformat()}", "booking_id": booking_id})


@meeting_bp.route('/rooms/<string:room_name>/extend', methods=['PUT'])
def extend_booking(room_name):
    room = mongo.db.meeting_rooms.find_one({"room_name": room_name})
    if not room or room.get('is_available'):
        return jsonify({"error": "Room is not currently booked"}), 404

    extra_minutes = request.json.get("extra_minutes")
    if not isinstance(extra_minutes, int):
        return jsonify({"error": "Please provide 'extra_minutes' as an integer"}), 400

    current_end_time = room.get('booked_until')
    if isinstance(current_end_time, str):
        current_end_time = datetime.datetime.fromisoformat(current_end_time)

    new_end_time = current_end_time + datetime.timedelta(minutes=extra_minutes)

    mongo.db.meeting_rooms.update_one(
        {"room_name": room_name},
        {"$set": {"booked_until": new_end_time.isoformat()}}
    )
    return jsonify({"message": f"Booking for {room_name} extended until {new_end_time.isoformat()}"})


@meeting_bp.route('/rooms/<string:booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    room_to_cancel = mongo.db.meeting_rooms.find_one({"booking_id": booking_id})
    if not room_to_cancel:
        return jsonify({"error": "Booking not found"}), 404

    room_name = room_to_cancel['room_name']
    mongo.db.meeting_rooms.update_one(
        {"booking_id": booking_id},
        {"$set": {
            "is_available": True,
            "booked_until": None,
            "booking_id": None
        }}
    )
    return jsonify({"message": f"Booking {booking_id} cancelled, {room_name} is now available"})


@meeting_bp.route('/rooms/<string:room_name>/equipment', methods=['GET'])
def get_equipment(room_name):
    room = mongo.db.meeting_rooms.find_one({"room_name": room_name})
    light = mongo.db.lights.find_one({"room": room_name}) or {"is_on": False}

    if not room:
        return jsonify({"error": "Invalid room"}), 400

    equipment_status = {
        "projector": room.get("has_projector", False),
        "projector_on": room.get("projector_on", False),
        "tv": room.get("has_tv", False),
        "tv_on": room.get("tv_on", False),
        "light": True,
        "light_on": light.get("is_on", False)
    }
    return jsonify({"equipment": equipment_status})

@meeting_bp.route('/rooms/<string:room_name>/prepare', methods=['POST'])
def prepare_room(room_name):
    room = mongo.db.meeting_rooms.find_one({"room_name": room_name})
    if not room:
        return jsonify({"error": "Invalid room"}), 404

    data = request.json
    update_doc = {}
    actions = []

    # --- Lights ---
    if "light" in data:
        mongo.db.lights.update_one(
            {"room": room_name},
            {"$set": {"is_on": bool(data["light"])}},
            upsert=True
        )
        actions.append(f"Lights {'ON' if data['light'] else 'OFF'}")

    # --- Projector ---
    if "projector" in data:
        if room.get("has_projector", False):
            update_doc["projector_on"] = bool(data["projector"])
            actions.append(f"Projector {'ON' if data['projector'] else 'OFF'}")
        else:
            actions.append("No projector in this room")

    # --- TV ---
    if "tv" in data:
        if room.get("has_tv", False):
            update_doc["tv_on"] = bool(data["tv"])
            actions.append(f"TV {'ON' if data['tv'] else 'OFF'}")
        else:
            actions.append("No TV in this room")

    # Apply DB updates for projector/TV
    if update_doc:
        mongo.db.meeting_rooms.update_one(
            {"room_name": room_name},
            {"$set": update_doc}
        )

    # --- Always return latest state from DB ---
    updated_room = mongo.db.meeting_rooms.find_one({"room_name": room_name}, {"_id": 0})
    light_status = mongo.db.lights.find_one({"room": room_name}, {"_id": 0})

    equipment_status = {
        "projector": updated_room.get("has_projector", False),
        "projector_on": updated_room.get("projector_on", False),
        "tv": updated_room.get("has_tv", False),
        "tv_on": updated_room.get("tv_on", False),
        "light": True,
        "light_on": light_status.get("is_on", False) if light_status else False
    }

    return jsonify({
        "message": f"{room_name} prepared",
        "actions": actions,
        "equipment": equipment_status
    })




@meeting_bp.route('/rooms/all/equipment', methods=['GET'])
def get_all_equipment_status():
    """Return unified equipment status for all meeting rooms."""
    lights = {doc['room']: doc['is_on'] for doc in mongo.db.lights.find({})}

    all_equipment = {}
    for room in mongo.db.meeting_rooms.find({}):
        room_name = room['room_name']
        light_status = lights.get(room_name, False)

        all_equipment[room_name] = {
            "equipment": {
                "projector": room.get("has_projector", False),
                "projector_on": room.get("projector_on", False),
                "tv": room.get("has_tv", False),
                "tv_on": room.get("tv_on", False),
                "light": True,
                "light_on": light_status
            }
        }
    return jsonify(all_equipment)
