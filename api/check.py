from flask import Flask, request, jsonify
from flask_cors import CORS
from storage import check_user_period

app = Flask(__name__)
CORS(app)


@app.route("/api/check", methods=["POST"])
def check():
    data = request.get_json() or {}
    login = data.get("login", "").strip()
    if not login:
        return jsonify({"ok": False, "error": "Login required"}), 400
    period = check_user_period(login)
    return jsonify({
        "ok": True,
        "login": login,
        "active": period["active"],
        "days_left": period.get("days_left", 0),
        "expires_at": period.get("expires_at"),
        "error": period.get("error"),
    }), 200
