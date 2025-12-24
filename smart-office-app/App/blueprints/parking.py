# App/blueprints/parking.py
import random
from datetime import datetime
from flask import Blueprint, jsonify, request
from .. import mongo  # from your App/__init__.py

parking_bp = Blueprint("parking", __name__, url_prefix="/api/parking")

# --- Constants ---
STATUSES = ["available", "reserved", "guest"]
USERS = ["Nelly", "Basil", "Admin", "Visitor1", "Guest2"]

# --- Seed once (idempotent) ---
def seed_parking_spots(count: int = 7):
    if mongo.db.parking_spots.count_documents({}) > 0:
        return

    docs = []
    for i in range(1, count + 1):
        status = random.choice(STATUSES)
        users = []
        if status != "available":
            users.append(random.choice(USERS))
        docs.append({
            "spot_id": i,
            "spot_name": f"A{i}",
            "status": status,
            "users": users
        })
    mongo.db.parking_spots.insert_many(docs)
    mongo.db.parking_spots.create_index("spot_id", unique=True)
    mongo.db.parking_spots.create_index("spot_name", unique=True)
    mongo.db.violations.create_index([("spot_id", 1), ("type", 1)], unique=True)

# --- Helpers ---
def _coerce_spot_identifier(data):
    spot_id = data.get("spot_id")
    spot_name = data.get("spot_name")
    if spot_id is not None:
        try:
            spot_id = int(spot_id)
        except (TypeError, ValueError):
            return None, (jsonify({"error": "spot_id must be an integer"}), 400)
        return {"spot_id": spot_id}, None
    if spot_name:
        return {"spot_name": str(spot_name)}, None
    return None, (jsonify({"error": "Provide spot_id or spot_name"}), 400)

# NEW: persist violations helpers (added, nothing removed)
def _upsert_violation(spot: dict, vtype: str, users, reason: str):
    users = sorted(list(set(users)))
    mongo.db.violations.update_one(
        {"spot_id": spot["spot_id"], "type": vtype},
        {"$set": {
            "spot_name": spot["spot_name"],
            "users": users,
            "reason": reason,
            "active": True,
            "updated_at": datetime.utcnow().isoformat(),
        },
         "$setOnInsert": {"created_at": datetime.utcnow().isoformat()}},
        upsert=True
    )

def _resolve_violation(spot_id: int, vtype: str | None = None):
    flt = {"spot_id": spot_id}
    if vtype:
        flt["type"] = vtype
    mongo.db.violations.update_many(
        flt,
        {"$set": {"active": False, "resolved_at": datetime.utcnow().isoformat()}}
    )

# ---------------- API ROUTES ----------------

@parking_bp.route("/spots/all", methods=["GET"])
def get_all_spots():
    docs = list(mongo.db.parking_spots.find({}, {"_id": 0}))
    return jsonify({"spots": docs})

@parking_bp.route("/spots/available", methods=["GET"])
def get_available_spots():
    docs = list(mongo.db.parking_spots.find({"status": "available"}, {"_id": 0}))
    return jsonify({"spots": docs})

@parking_bp.route("/my-reservations", methods=["GET"])
def my_reservations():
    user = request.args.get("user")
    if not user:
        return jsonify({"error": "A 'user' query parameter is required"}), 400

    docs = list(mongo.db.parking_spots.find({"users": user}, {"_id": 0, "spot_name": 1, "spot_id": 1}))
    return jsonify({"user": user, "reservations": [d["spot_name"] for d in docs]})

@parking_bp.route("/checkin", methods=["POST"])
def checkin_spot():
    data = request.json or {}
    user = data.get("user")
    if not user:
        return jsonify({"error": "user is required"}), 400

    flt, err = _coerce_spot_identifier(data)
    if err:
        return err

    spot = mongo.db.parking_spots.find_one(flt)
    if not spot:
        return jsonify({"error": "Invalid spot"}), 404

    if spot["status"] in ("reserved", "guest"):
        mongo.db.checkins.insert_one({
            "spot_id": spot["spot_id"],
            "spot_name": spot["spot_name"],
            "user": user,
            "timestamp": datetime.utcnow().isoformat()
        })

        distinct_users = {d["user"] for d in mongo.db.checkins.find(
            {"spot_id": spot["spot_id"]}, {"_id": 0, "user": 1}
        )}
        if len(distinct_users) > 1:
            _upsert_violation(
                spot,
                vtype="multi_checkin",
                users=distinct_users,
                reason="Multiple users checked in to the same spot"
            )
        else:
            _resolve_violation(spot["spot_id"], "multi_checkin")

        if user in spot.get("users", []):
            return jsonify({"message": f"Check-in successful for {user} at {spot['spot_name']}"}), 200
        else:
            return jsonify({
                "error": f"Spot {spot['spot_name']} reserved for {', '.join(spot.get('users', []))}, not {user}"
            }), 403

    return jsonify({"error": f"Spot {spot['spot_name']} is not reserved/guest"}), 400

@parking_bp.route("/reserve", methods=["POST"])
def reserve_spot():
    data = request.json or {}
    user = data.get("user")
    if not user:
        return jsonify({"error": "user is required"}), 400

    flt, err = _coerce_spot_identifier(data)
    if err:
        return err

    spot = mongo.db.parking_spots.find_one(flt)
    if not spot:
        return jsonify({"error": "Invalid spot"}), 404

    users = spot.get("users", [])

    attempt_doc = {"user": user, "ts": datetime.utcnow().isoformat()}
    mongo.db.parking_spots.update_one(flt, {"$push": {"attempts": attempt_doc}})

    if spot.get("status") == "available" or not users:
        mongo.db.parking_spots.update_one(
            flt,
            {"$set": {"status": "reserved", "users": [user]}}
        )
        _resolve_violation(spot["spot_id"], "double_booking")
        return jsonify({"message": f"Spot {spot['spot_name']} reserved for {user}"}), 200

    if user in users:
        return jsonify({"message": f"Spot {spot['spot_name']} already reserved for {user}"}), 200

    all_users = set(users) | {user}
    _upsert_violation(
        spot,
        vtype="double_booking",
        users=all_users,
        reason="Conflicting reservations (double booking attempt)"
    )
    return jsonify({
        "error": f"Spot {spot['spot_name']} is already reserved by {', '.join(users)}"
    }), 409

@parking_bp.route("/guest-pass", methods=["POST"])
def guest_spot():
    data = request.json or {}
    user = data.get("user")
    if not user:
        return jsonify({"error": "user is required"}), 400

    flt, err = _coerce_spot_identifier(data)
    if err:
        return err

    spot = mongo.db.parking_spots.find_one(flt)
    if not spot:
        return jsonify({"error": "Invalid spot"}), 404
    if spot["status"] != "available":
        return jsonify({"error": f"Spot {spot['spot_name']} is not available"}), 409

    mongo.db.parking_spots.update_one(flt, {"$set": {"status": "guest", "users": [user]}})
    return jsonify({"message": f"Spot {spot['spot_name']} assigned as guest pass for {user}!"})

@parking_bp.route("/violations", methods=["GET"])
def get_violations():
    spot_filter = request.args.get("spot_id", type=int)
    violations = []
    spots = list(mongo.db.parking_spots.find({}, {"_id": 0}))

    for spot in spots:
        if spot_filter and spot["spot_id"] != spot_filter:
            continue

        status = spot.get("status")
        users = set(spot.get("users", []))
        attempt_users = {a.get("user") for a in spot.get("attempts", []) if a.get("user")}
        all_reservation_users = users | attempt_users

        # --- Scenario 1: Double booking / conflicting reservations ---
        if status == "reserved" and len(all_reservation_users) > 1:
            violations.append({
                "spot_id": spot["spot_id"],
                "users": sorted(all_reservation_users),
                "violation_reason": "Conflicting reservations (double booking attempt)"
            })

    # --- Scenario 2: Multiple check-ins ---
    checkins = list(mongo.db.checkins.find({}, {"_id": 0}))
    checkin_map = {}
    for ci in checkins:
        sid = ci["spot_id"]
        if spot_filter and sid != spot_filter:
            continue
        checkin_map.setdefault(sid, set()).add(ci["user"])
    for sid, u in checkin_map.items():
        if len(u) > 1:
            violations.append({
                "spot_id": sid,
                "users": sorted(u),
                "violation_reason": "Multiple users checked in to same spot"
            })

    return jsonify({"count": len(violations), "violations": violations})

# NEW: list active persisted violations
@parking_bp.route("/violations/active", methods=["GET"])
def get_active_violations():
    docs = list(mongo.db.violations.find({"active": True}, {"_id": 0}))
    return jsonify({"count": len(docs), "violations": docs})

# NEW: resolve persisted violations (by spot_id, optional type)
@parking_bp.route("/violations/resolve", methods=["POST"])
def resolve_violation():
    data = request.json or {}
    spot_id = data.get("spot_id")
    vtype = data.get("type")  # "double_booking" | "multi_checkin" | None
    if spot_id is None:
        return jsonify({"error": "spot_id is required"}), 400
    _resolve_violation(int(spot_id), vtype)
    return jsonify({"message": "resolved"}), 200

# --- Reset DB on first run (single hook) ---
_seeded = False
@parking_bp.before_app_request
def _ensure_seed_once():
    global _seeded
    if not _seeded:
        mongo.db.parking_spots.delete_many({})
        mongo.db.checkins.delete_many({})
        seed_parking_spots()
        _seeded = True
