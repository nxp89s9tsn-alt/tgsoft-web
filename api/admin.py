from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, hashlib
from datetime import datetime, timezone, timedelta

ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "tgsoft_admin_2024")
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

@app.route("/api/admin", methods=["POST", "GET"])
def admin():
    data = request.get_json(force=True, silent=True) or {}
    admin_login = data.get("admin_login", "")
    admin_password = data.get("admin_password", "")
    action = data.get("action", "")

    if admin_login != ADMIN_LOGIN or admin_password != ADMIN_PASSWORD:
        return jsonify({"ok": False, "error": "Access denied"}), 403

    if action == "list":
        safe = []
        for u in _load():
            safe.append({
                "login": u.get("login"), "status": u.get("status"),
                "period_days": u.get("period_days", 0),
                "activated_at": u.get("activated_at"), "expires_at": u.get("expires_at"),
                "last_login": u.get("last_login"), "machine_id": u.get("machine_id"),
                "created_at": u.get("created_at"),
            })
        return jsonify({"ok": True, "users": safe}), 200

    elif action == "set_period":
        login = data.get("login", "")
        days = int(data.get("days", 0))
        if not login or days <= 0:
            return jsonify({"ok": False, "error": "Login and days required"}), 400
        users = _load()
        now = datetime.now(timezone.utc)
        for u in users:
            if u["login"] == login:
                u["period_days"] = days
                u["activated_at"] = now.isoformat()
                u["expires_at"] = (now + timedelta(days=days)).isoformat()
                u["status"] = "active"
                _save(users)
                return jsonify({"ok": True, "login": login, "days": days}), 200
        return jsonify({"ok": False, "error": "User not found"}), 404

    elif action == "revoke":
        login = data.get("login", "")
        users = _load()
        for u in users:
            if u["login"] == login:
                u["status"] = "revoked"
                _save(users)
                return jsonify({"ok": True, "login": login}), 200
        return jsonify({"ok": False, "error": "User not found"}), 404

    elif action == "info":
        user = _find(data.get("login", ""))
        if user:
            return jsonify({"ok": True, "login": user.get("login"), "status": user.get("status"),
                "period_days": user.get("period_days", 0), "expires_at": user.get("expires_at"),
                "last_login": user.get("last_login"), "machine_id": user.get("machine_id")}), 200
        return jsonify({"ok": False, "error": "User not found"}), 404

    return jsonify({"ok": False, "error": "Unknown action"}), 400

handler = app
