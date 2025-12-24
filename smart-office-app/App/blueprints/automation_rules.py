from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from .. import mongo  # uses your existing mongo from App/__init__.py
from flask import request, jsonify
from bson import ObjectId

# URL base: /api/automation
automation_rules_bp = Blueprint("automation_rules", __name__, url_prefix="/api/automation")


@automation_rules_bp.route("/rules/create", methods=["POST"])
def create_rule():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    actions = body.get("actions")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name is required (non-empty string)"}), 400
    if not isinstance(actions, list) or len(actions) == 0:
        return jsonify({"error": "actions is required (non-empty array)"}), 400
#-----------------------------------------------

    for i, a in enumerate(actions, start=1):
        if not isinstance(a, dict):
            return jsonify({"error": f"action #{i} must be an object"}), 400

        has_scene = bool(a.get("scene_id"))
        has_device = bool(a.get("device_id")) and bool(a.get("action"))

        if not has_scene and not has_device:
            return jsonify({"error": f"action #{i} must include scene_id OR (device_id and action)"}), 400
        if has_scene and has_device:
            return jsonify({"error": f"action #{i} cannot include both scene_id AND device fields"}), 400

        # allow optional "state" as dict (don’t enforce)
        if "state" in a and not isinstance(a["state"], dict):
            return jsonify({"error": f"action #{i} 'state' must be an object if provided"}), 400

    enabled = bool(body.get("enabled", True))
    conditions = body.get("conditions", [])
    if not isinstance(conditions, list):
        conditions = []

    schedule = body.get("schedule")
    if not isinstance(schedule, dict):
        schedule = None  # ignore if wrong type

    doc = {
        "name": name.strip(),
        "enabled": enabled,
        "conditions": conditions,
        "actions": actions,
        "schedule": schedule,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    res = mongo.db.automation_rules.insert_one(doc)

    return jsonify({"id": str(res.inserted_id), "message": "rule created"}), 201


# helper to expose Mongo _id as "id"
def _public_rule(doc):
    d = dict(doc)
    d["id"] = str(d.pop("_id"))
    return d


@automation_rules_bp.route("/rules/active", methods=["GET"])
def list_active_rules():
    """Return all enabled automation rules."""
    docs = list(mongo.db.automation_rules.find({"enabled": True}))
    rules = [_public_rule(d) for d in docs]
    return jsonify({"count": len(rules), "rules": rules}), 200


@automation_rules_bp.route("/triggers/motion", methods=["POST"])
def trigger_motion():
    b = request.get_json(silent=True) or {}
    sid = b.get("sensor_id")
    det = b.get("detected")
    zone = b.get("zone")
    meta = b.get("metadata") or {}
    ts   = b.get("timestamp")

    if not isinstance(sid, str) or not sid.strip():
        return jsonify({"error": "sensor_id required"}), 400
    if not isinstance(det, bool):
        return jsonify({"error": "detected must be boolean"}), 400

    # parse timestamp (ISO); fallback to server UTC
    now = datetime.utcnow()
    if isinstance(ts, str):
        try:
            t = ts.rstrip("Z")
            if ts.endswith("Z"):
                t += "+00:00"
            dt = datetime.fromisoformat(t)
            now = dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt
        except Exception:
            pass

    # log raw event
    mongo.db.automation_events.insert_one({
        "type": "motion", "sensor_id": sid, "detected": det,
        "zone": zone, "metadata": meta, "timestamp": now.isoformat()
    })
    if not det:
        return jsonify({"processed": False, "reason": "no motion"}), 200

    # helpers
    def hhmm(s):
        try: h, m = map(int, (s or "0:0").split(":")); return h*60 + m
        except: return None

    nowm, matched, actions = now.hour*60 + now.minute, [], []

    # evaluate enabled rules (support: motion/zone, time after/before, lux lte/gte)
    for r in mongo.db.automation_rules.find({"enabled": True}):
        ok = True
        for c in (r.get("conditions") or []):
            t = c.get("type")
            if t == "motion" and c.get("zone") and c["zone"] != zone:
                ok = False; break
            if t == "time":
                a = hhmm(c.get("after"))
                b4 = hhmm(c.get("before") or "23:59")
                if a is not None and nowm < a:  ok = False; break
                if b4 is not None and nowm > b4: ok = False; break
            if t == "lux":
                lux = meta.get("lux")
                if lux is None or ("lte" in c and not (lux <= c["lte"])) or ("gte" in c and not (lux >= c["gte"])):
                    ok = False; break
        if not ok:
            continue

        # expand actions (scene → device actions) and keep device actions
        for a in (r.get("actions") or []):
            if isinstance(a, dict) and a.get("scene_id"):
                sc = None
                try:   sc = mongo.db.automation_scenes.find_one({"_id": ObjectId(a["scene_id"])})
                except Exception: sc = mongo.db.automation_scenes.find_one({"name": a["scene_id"]})
                if sc:
                    for d in sc.get("devices", []):
                        actions.append({"device_id": d.get("device_id"), "action": "set_state", "state": d.get("state", {})})
            elif isinstance(a, dict) and a.get("device_id") and a.get("action"):
                actions.append(a)
        matched.append(str(r.get("_id")))

    # log execution summary
    mongo.db.automation_executions.insert_one({
        "event": {"type": "motion", "sensor_id": sid, "zone": zone, "metadata": meta, "timestamp": now.isoformat()},
        "matched_rules": matched, "actions_fired": actions, "created_at": datetime.utcnow().isoformat()
    })
    return jsonify({"processed": True, "matched_rules": matched, "actions_fired": actions}), 200


# tiny heuristic used if executions don't already contain energy_kwh_est
def _estimate_kwh(action: dict) -> float:
    dev = (action.get("device_id") or "")
    act = action.get("action")
    st  = action.get("state") or {}
    k = 0.0
    if act == "turn_off" or st.get("power") == "off":
        k += 0.06 if dev.startswith("light.") else (0.15 if dev.startswith("climate.") else 0.05)
    if act == "set_brightness":
        k += 0.02
    if act == "set_mode" and st.get("mode") in ("eco", "auto_eco"):
        k += 0.3
    if act in ("set_temp", "set_temperature"):
        t = st.get("target")
        if isinstance(t, (int, float)) and (t >= 24 or t <= 20):
            k += 0.3
    return round(k, 4)


@automation_rules_bp.route("/energy-savings", methods=["GET"])
def energy_savings():
    """
    GET params (optional):
      - days: int (default 7)
    Returns total kWh + breakdown by date and device from automation_executions.
    """
    days = request.args.get("days", default=7, type=int)
    since = datetime.utcnow() - timedelta(days=max(days, 1))

    docs = list(mongo.db.automation_executions.find().sort("created_at", -1))
    total, by_day, by_device, execs = 0.0, {}, {}, 0

    for ex in docs:
        # filter by created_at (stored as ISO string)
        try:
            created = datetime.fromisoformat((ex.get("created_at") or "").replace("Z", "+00:00"))
        except Exception:
            created = None
        if created and created < since:
            continue

        execs += 1
        # prefer stored estimate, else compute from actions
        kwh = ex.get("energy_kwh_est")
        if not isinstance(kwh, (int, float)):
            kwh = sum(_estimate_kwh(a) for a in (ex.get("actions_fired") or []))
        total += kwh

        day = (created.date().isoformat() if created else "unknown")
        by_day[day] = round(by_day.get(day, 0.0) + kwh, 4)

        for a in (ex.get("actions_fired") or []):
            dev = (a.get("device_id") or "scene/unknown")
            by_device[dev] = round(by_device.get(dev, 0.0) + _estimate_kwh(a), 4)

    # shape response
    return jsonify({
        "window_days": days,
        "count_executions": execs,
        "total_kwh": round(total, 4),
        "by_day": [{"date": d, "kwh": by_day[d]} for d in sorted(by_day.keys())],
        "by_device": [{"device_id": d, "kwh": by_device[d]} for d in sorted(by_device.keys())]
    }), 200


@automation_rules_bp.route("/scenes/create", methods=["POST"])
def create_scene():
    """
    Create an environmental scene.
    Required: name (str), devices (list of {device_id, state})
    """
    body = request.get_json(silent=True) or {}

    name = body.get("name")
    devices = body.get("devices")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name is required"}), 400
    if not isinstance(devices, list) or len(devices) == 0:
        return jsonify({"error": "devices must be a non-empty array"}), 400

    # validate devices
    for i, d in enumerate(devices, start=1):
        if not isinstance(d, dict):
            return jsonify({"error": f"device #{i} must be an object"}), 400
        if not d.get("device_id") or not isinstance(d["device_id"], str):
            return jsonify({"error": f"device #{i} missing valid device_id"}), 400
        if "state" in d and not isinstance(d["state"], dict):
            return jsonify({"error": f"device #{i} 'state' must be an object"}), 400

    doc = {
        "name": name.strip(),
        "devices": devices,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    res = mongo.db.automation_scenes.insert_one(doc)

    return jsonify({"id": str(res.inserted_id), "message": "scene created"}), 201
