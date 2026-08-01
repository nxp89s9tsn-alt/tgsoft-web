from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os
from datetime import datetime, timezone

_JSON_PATH = "/tmp/tgsoft_users.json"

def _load():
    try:
        with open(_JSON_PATH, "r") as f: return json.load(f)
    except: return []
def _find(login):
    for u in _load():
        if u.get("login") == login: return u
    return None
def _check_period(login):
    user = _find(login)
    if not user: return {"active": False, "days_left": 0, "error": "user_not_found"}
    if user.get("status") == "revoked": return {"active": False, "days_left": 0, "error": "revoked"}
    if not user.get("expires_at"): return {"active": False, "days_left": 0, "error": "not_activated"}
    now = datetime.now(timezone.utc)
    expires = datetime.fromisoformat(user["expires_at"])
    if now > expires: return {"active": False, "days_left": 0, "error": "expired"}
    return {"active": True, "days_left": max(0, (expires - now).days), "expires_at": user["expires_at"]}

app = Flask(__name__)
CORS(app)

@app.route("/api/check", methods=["POST", "GET"])
def check():
    data = request.get_json(force=True, silent=True) or {}
    login = data.get("login", "").strip()
    if not login:
        return jsonify({"ok": False, "error": "Login required"}), 400
    period = _check_period(login)
    return jsonify({
        "ok": True, "login": login, "active": period["active"],
        "days_left": period.get("days_left", 0), "expires_at": period.get("expires_at"),
        "error": period.get("error"),
    }), 200

handler = app
