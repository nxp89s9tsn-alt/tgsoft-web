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

app = Flask(__name__)
CORS(app)

@app.route("/api/register", methods=["POST", "GET"])
def register():
    data = request.get_json(force=True, silent=True) or {}
    login = data.get("login", "").strip()
    password = data.get("password", "").strip()
    if not login or not password:
        return jsonify({"ok": False, "error": "Login and password required"}), 400
    if len(login) < 3:
        return jsonify({"ok": False, "error": "Login too short"}), 400
    if len(password) < 4:
        return jsonify({"ok": False, "error": "Password too short"}), 400
    if _find(login):
        return jsonify({"ok": False, "error": "User already exists"}), 409
    users = _load()
    users.append({
        "login": login, "password_hash": _hash_pw(password),
        "period_days": 0, "activated_at": None, "expires_at": None,
        "status": "inactive", "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None, "machine_id": None,
    })
    _save(users)
    return jsonify({"ok": True, "login": login}), 201

# Vercel entry point
handler = app
