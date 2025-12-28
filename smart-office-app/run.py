import threading
from App import create_app, mongo
from App.blueprints.control import schedule_loop
from App.blueprints.energy import energy_loop
from App.blueprints.meeting_rooms import seed_meeting_rooms
from App.blueprints.parking import seed_parking_spots
from App.blueprints.automation_rules import automation_rules_bp
from prometheus_client import generate_latest  

app = create_app()
# --- 2. (Health & Metrics) ---

# 1. מונה בקשות - מחולק לפי נתיב (Endpoint)
# זה יראה בפלט בדיוק לאן המשתמשים נכנסו
REQUEST_COUNT = Counter(
    'smart_office_requests_total', 
    'Total number of requests by endpoint',
    ['method', 'endpoint']
)

# 2. מדד זמן ריצה - כמה זמן האפליקציה באוויר
APP_START_TIME = time.time()
UPTIME_GAUGE = Gauge(
    'smart_office_uptime_seconds', 
    'Number of seconds the app has been running'
)

# 3. היסטוגרמה - מודד כמה זמן לוקח לכל בקשה להתבצע (Latency)
# זהו מדד ה-DevOps היוקרתי ביותר
REQUEST_LATENCY = Histogram(
    'smart_office_request_duration_seconds', 
    'Time spent processing request'
)

@app.route('/metrics')
def metrics():
    # עדכון זמן הריצה לפני שליחת הפלט
    UPTIME_GAUGE.set(time.time() - APP_START_TIME)
    return generate_latest(), 200

# Liveness Probe
@app.route('/health/live')
def health_live():
    return {"status": "alive"}, 200

# Readiness Probe
@app.route('/health/ready')
def health_ready():
    try:
        mongo.db.command('ping')
        return {"status": "ready", "db": "connected"}, 200
    except Exception as e:
        return {"status": "not ready", "error": str(e)}, 503
# -----------------------------------------------------

if __name__ == '__main__':
    with app.app_context():

        # Clear and re-seed lights + room_states
        mongo.db.lights.delete_many({})
        mongo.db.room_states.delete_many({})

        initial_rooms = ['london', 'boot', 'meeting']

        lights_to_insert = [{"room": name, "is_on": False} for name in initial_rooms]
        mongo.db.lights.insert_many(lights_to_insert)

        states_to_insert = [{"room": name, "ac_on": False, "temperature": None} for name in initial_rooms]
        mongo.db.room_states.insert_many(states_to_insert)


        mongo.db.meeting_rooms.delete_many({})   # wipe old bookings
        seed_meeting_rooms()                     # re-seed as available

        mongo.db.parking_spots.delete_many({})  # clear existing spots
        seed_parking_spots()  # insert new random spots


    # Start background threads for HVAC scheduling and energy monitoring
    threading.Thread(target=schedule_loop, args=(app,), daemon=True).start()
    threading.Thread(target=energy_loop, args=(app,), daemon=True).start()

    # Start the Flask development server
    app.run(host="0.0.0.0", port=5000, debug=True)
