from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, hashlib
from datetime import datetime, timezone

_JSON_PATH = "/tmp/tgsoft_users.json"

def _hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def _load():
    try:
        with open(_JSON_PATH, "r") as f: return json.load(f)
    except: return []
def _save(users):
    with open(_JSON_PATH, "w") as f: json.dump(users, f)
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
    if now > expires:
        users = _load()
        for u in users:
            if u["login"] == login: u["status"] = "expired"
        _save(users)
        return {"active": False, "days_left": 0, "error": "expired"}
    return {"active": True, "days_left": max(0, (expires - now).days), "expires_at": user["expires_at"]}

app = Flask(__name__)
CORS(app)

@app.route("/api/login", methods=["POST", "GET"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    login = data.get("login", "").strip()
    password = data.get("password", "").strip()
    machine_id = data.get("machine_id", "").strip()
    if not login or not password:
        return jsonify({"ok": False, "error": "Login and password required"}), 400
    user = _find(login)
    if not user or user.get("password_hash") != _hash_pw(password):
        return jsonify({"ok": False, "error": "Invalid credentials"}), 401
    users = _load()
    for u in users:
        if u["login"] == login:
            u["last_login"] = datetime.now(timezone.utc).isoformat()
            if machine_id: u["machine_id"] = machine_id
    _save(users)
    period = _check_period(login)
    return jsonify({
        "ok": True, "login": login, "active": period["active"],
        "days_left": period.get("days_left", 0), "expires_at": period.get("expires_at"),
        "error": period.get("error"),
    }), 200

handler = app
