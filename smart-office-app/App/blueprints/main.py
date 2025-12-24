# App/blueprints/main.py
from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)

@main_bp.route('/')
def welcome():
    return render_template("welcome.html")

@main_bp.route('/control')
def control():
    return render_template("index.html")

@main_bp.route('/control3d')
def control3d():
    return render_template("control_3d.html")

@main_bp.route("/parking")
def parking():
    return render_template("parking.html")

@main_bp.route("/wellness")
def wellness():
    return render_template("wellness.html")