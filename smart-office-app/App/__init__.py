# App/__init__.py
import os
from flask import Flask
from flask_pymongo import PyMongo

# 1. Create a global mongo instance that blueprints can import.
# It will be configured inside the factory.
mongo = PyMongo()


def create_app():
    """Application factory function."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder='../templates'
    )

    # 2. --- MongoDB Configuration ---
    # This connection string points to your local MongoDB server
    # and creates a database named 'smart_office'.
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/smart_office")

    # 3. Initialize the PyMongo extension with your app.
    mongo.init_app(app)

    # --- Import & Register Blueprints ---
    # This part stays the same. The blueprints will be updated separately.
    from .blueprints.main import main_bp
    from .blueprints.control import control_bp
    from .blueprints.energy import energy_bp
    from .blueprints.parking import parking_bp
    from .blueprints.meeting_rooms import meeting_bp
    from .blueprints.wellness import wellness_bp
    from .blueprints.automation_rules import automation_rules_bp

    # Register the blueprints with the app
    app.register_blueprint(main_bp)
    app.register_blueprint(control_bp)
    app.register_blueprint(energy_bp)
    app.register_blueprint(parking_bp)
    app.register_blueprint(meeting_bp)
    app.register_blueprint(wellness_bp)
    app.register_blueprint(automation_rules_bp)

    return app