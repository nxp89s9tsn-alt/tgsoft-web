from flask import Flask, request, jsonify
from flask_cors import CORS
from storage import create_user, find_user

app = Flask(__name__)
CORS(app)


def handler(req):
    with app.test_request_context(req.path, method=req.method, json=req.get_json()):
        return app.full_dispatch_request()


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    login = data.get("login", "").strip()
    password = data.get("password", "").strip()
    if not login or not password:
        return jsonify({"ok": False, "error": "Login and password required"}), 400
    if len(login) < 3:
        return jsonify({"ok": False, "error": "Login too short"}), 400
    if len(password) < 4:
        return jsonify({"ok": False, "error": "Password too short"}), 400
    if find_user(login):
        return jsonify({"ok": False, "error": "User already exists"}), 409
    if create_user(login, password):
        return jsonify({"ok": True, "login": login}), 201
    return jsonify({"ok": False, "error": "Failed"}), 500
