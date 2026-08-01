"""POST /api/login — verify user. Body: {login, password, machine_id}"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from storage import verify_user, update_user_login, check_user_period

app = Flask(__name__)
CORS(app)

@app.route("/api/login", methods=["POST"])
def handle():
    data = request.get_json() or {}
    login = data.get("login", "").strip()
    password = data.get("password", "").strip()
    machine_id = data.get("machine_id", "").strip()

    if not login or not password:
        return jsonify({"ok": False, "error": "Login and password required"}), 400

    user = verify_user(login, password)
    if not user:
        return jsonify({"ok": False, "error": "Invalid credentials"}), 401

    update_user_login(login, machine_id)

    period = check_user_period(login)

    return jsonify({
        "ok": True,
        "login": login,
        "active": period["active"],
        "days_left": period.get("days_left", 0),
        "expires_at": period.get("expires_at"),
        "error": period.get("error"),
    }), 200

if __name__ == "__main__":
    app.run()
