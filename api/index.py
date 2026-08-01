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

# ===== REGISTER =====
@app.route("/api/register", methods=["POST"])
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

# ===== LOGIN =====
@app.route("/api/login", methods=["POST"])
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

# ===== CHECK =====
@app.route("/api/check", methods=["POST"])
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

# ===== ADMIN =====
@app.route("/api/admin", methods=["POST"])
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

# ===== Health check =====
@app.route("/api", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "TGSoft API"}), 200

handler = app
