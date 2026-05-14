import os
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from .fiat import Fiat, load_env
from .users import VALID_USERS

print(f"Looking for .env file at: {Path(__file__).resolve().parents[1] / '.env'}")
load_env(Path(__file__).resolve().parents[1] / ".env")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "replace-this-with-a-random-secret-key")
app.config["AUTH_TOKEN_MAX_AGE"] = 3600  # seconds

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
fiat_client = Fiat()


def generate_auth_token(username: str) -> str:
    return serializer.dumps({"username": username})


def verify_auth_token(token: str) -> str | None:
    try:
        data = serializer.loads(token, max_age=app.config["AUTH_TOKEN_MAX_AGE"])
        return data.get("username")
    except (BadSignature, SignatureExpired):
        return None


def login_required(view):
    def wrapped_view(*args, **kwargs):
        auth_token = request.cookies.get("auth_token")
        username = verify_auth_token(auth_token) if auth_token else None
        if not username:
            return redirect(url_for("login", next=request.path))
        return view(username, *args, **kwargs)

    wrapped_view.__name__ = view.__name__
    return wrapped_view


@app.route("/login", methods=["GET", "POST"])
def login():
    auth_token = request.cookies.get("auth_token")
    if auth_token and verify_auth_token(auth_token):
        return redirect(url_for("main"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        expected_password = VALID_USERS.get(username)

        if expected_password and password == expected_password:
            token = generate_auth_token(username)
            response = make_response(redirect(url_for("main")))
            response.set_cookie(
                "auth_token",
                token,
                httponly=True,
                samesite="Lax",
                max_age=app.config["AUTH_TOKEN_MAX_AGE"],
            )
            return response
        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    response = make_response(redirect(url_for("login")))
    response.delete_cookie("auth_token")
    return response


@app.route("/status")
@login_required
def status(username: str):
    ev_status = get_ev_status(username)
    vehicle_info = get_vehicle_info(username)
    return jsonify({
        "ev_status": ev_status,
        "vehicle_info": vehicle_info,
    })


def get_ev_status(username: str) -> dict:
    result = fiat_client.update()

    door_driver_status = "LOCKED" if result["door_driver_locked"] else "UNLOCKED"
    door_passenger_status = "LOCKED" if result["door_passenger_locked"] else "UNLOCKED"
    overall_lock_status = "LOCKED" if door_driver_status == "LOCKED" and door_passenger_status == "LOCKED" else "UNLOCKED"

    window_driver_status = "CLOSED" if result["window_driver_closed"] else "OPEN"
    window_passenger_status = "CLOSED" if result["window_passenger_closed"] else "OPEN"
    overall_window_status = "CLOSED" if window_driver_status == "CLOSED" and window_passenger_status == "CLOSED" else "OPEN"

    return {
        "charging_status": result["charging_status"],
        "state_of_charge": result["state_of_charge"],
        "lock_status": overall_lock_status,
        "door_lock_status": overall_lock_status,
        "door_lock_left_status": door_driver_status,
        "door_lock_right_status": door_passenger_status,
        "window_lock_status": overall_window_status,
        "window_lock_left_status": window_driver_status,
        "window_lock_right_status": window_passenger_status,
        "remaining_distance": f"{result['remaining_range']} km",
    }


def get_vehicle_info(username: str) -> dict:
    vehicle = fiat_client.vehicle
    return {
        "vin": fiat_client.vin,
        "nickname": getattr(vehicle, "nickname", None) or getattr(vehicle, "name", None) or "N/A",
        "odometer": (
            getattr(vehicle, "odometer", None)
            or getattr(vehicle, "odometer_value", None)
            or getattr(vehicle, "distance_total", None)
            or getattr(vehicle, "mileage", None)
            or "N/A"
        ),
        "odometer_unit": (
            getattr(vehicle, "odometer_unit", None)
            or getattr(vehicle, "distance_unit", None)
            or getattr(vehicle, "mileage_unit", None)
            or "km"
        ),
        "last_update": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }


@app.route("/")
@login_required
def main(username: str):
    return render_template("main.html", username=username)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
