# App/blueprints/energy.py
import datetime
import time
from flask import Blueprint, jsonify
from .. import mongo  # Import the mongo instance from App/__init__.py

energy_bp = Blueprint("energy", __name__, url_prefix="/api/environment/energy")


def get_or_create_today_usage():
    today_str = datetime.date.today().isoformat()
    usage_doc = mongo.db.energy_usage.find_one({"date": today_str})

    if not usage_doc:
        # If no document exists for today, create a new one
        new_usage = {
            "date": today_str,
            "lights_kwh": 0.0,
            "ac_kwh": 0.0,
            "total_kwh": 0.0
        }
        # Insert the new document into the 'energy_usage' collection
        mongo.db.energy_usage.insert_one(new_usage)
        return new_usage

    return usage_doc

#GET /api/environment/energy/usage - Monitor energy consumption
@energy_bp.route('/usage', methods=['GET'])
def get_energy_usage():
    """API endpoint to get today's energy usage."""
    usage = get_or_create_today_usage()

    # MongoDB's _id is not JSON serializable by default, so we convert it to a string.
    if '_id' in usage:
        usage['_id'] = str(usage['_id'])

    return jsonify({
        "lights_today_kwh": usage.get("lights_kwh", 0),
        "ac_today_kwh": usage.get("ac_kwh", 0),
        "total_today_kwh": usage.get("total_kwh", 0),
    })


def energy_loop(app):
    while True:
        with app.app_context():
            usage = get_or_create_today_usage()

            lights_on = mongo.db.lights.count_documents({"is_on": True})
            ac_on = mongo.db.room_states.count_documents({"ac_on": True})

            lights_power_kw = lights_on * 0.01
            ac_power_kw = ac_on * 0.02

            interval_hours = 30 / 3600
            lights_kwh_increment = lights_power_kw * interval_hours
            ac_kwh_increment = ac_power_kw * interval_hours

            mongo.db.energy_usage.update_one(
                {"_id": usage["_id"]},
                {
                    "$inc": {
                        "lights_kwh": lights_kwh_increment,
                        "ac_kwh": ac_kwh_increment,
                        "total_kwh": lights_kwh_increment + ac_kwh_increment
                    }
                }
            )

        time.sleep(30)