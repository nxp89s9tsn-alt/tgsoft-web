from flask import Flask, request, jsonify
from flask_cors import CORS
from storage import is_admin, get_all_users, set_user_period, revoke_user, find_user

app = Flask(__name__)
CORS(app)


@app.route("/api/admin", methods=["POST"])
def admin():
    data = request.get_json() or {}
    admin_login = data.get("admin_login", "")
    admin_password = data.get("admin_password", "")
    action = data.get("action", "")

    if not is_admin(admin_login, admin_password):
        return jsonify({"ok": False, "error": "Access denied"}), 403

    if action == "list":
        users = get_all_users()
        safe = []
        for u in users:
            safe.append({
                "login": u.get("login"),
                "status": u.get("status"),
                "period_days": u.get("period_days", 0),
                "activated_at": u.get("activated_at"),
                "expires_at": u.get("expires_at"),
                "last_login": u.get("last_login"),
                "machine_id": u.get("machine_id"),
                "created_at": u.get("created_at"),
            })
        return jsonify({"ok": True, "users": safe}), 200

    elif action == "set_period":
        login = data.get("login", "")
        days = int(data.get("days", 0))
        if not login or days <= 0:
            return jsonify({"ok": False, "error": "Login and days required"}), 400
        if set_user_period(login, days):
            return jsonify({"ok": True, "login": login, "days": days}), 200
        return jsonify({"ok": False, "error": "User not found"}), 404

    elif action == "revoke":
        login = data.get("login", "")
        if not login:
            return jsonify({"ok": False, "error": "Login required"}), 400
        if revoke_user(login):
            return jsonify({"ok": True, "login": login}), 200
        return jsonify({"ok": False, "error": "User not found"}), 404

    elif action == "info":
        login = data.get("login", "")
        user = find_user(login)
        if user:
            return jsonify({
                "ok": True,
                "login": user.get("login"),
                "status": user.get("status"),
                "period_days": user.get("period_days", 0),
                "expires_at": user.get("expires_at"),
                "last_login": user.get("last_login"),
                "machine_id": user.get("machine_id"),
            }), 200
        return jsonify({"ok": False, "error": "User not found"}), 404

    return jsonify({"ok": False, "error": "Unknown action"}), 400
