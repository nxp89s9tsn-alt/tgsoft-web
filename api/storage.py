"""
Storage — works without Vercel KV using JSON file fallback.
Automatically detects: KV if env vars present, otherwise JSON file.
"""
import json
import os
import hashlib
from datetime import datetime, timezone, timedelta

ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "tgsoft_admin_2024")

# JSON file fallback path (writable temp dir on Vercel)
_JSON_PATH = "/tmp/tgsoft_users.json"


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _kv_get(key: str):
    url = os.environ.get("KV_REST_API_URL", "")
    token = os.environ.get("KV_REST_API_TOKEN", "")
    if not url or not token:
        return None
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{url}/get/{key}",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            result = data.get("result")
            if result and result != "null":
                return json.loads(result)
    except:
        pass
    return None


def _kv_set(key: str, value):
    url = os.environ.get("KV_REST_API_URL", "")
    token = os.environ.get("KV_REST_API_TOKEN", "")
    if not url or not token:
        return False
    try:
        import urllib.request
        body = json.dumps(value).encode()
        req = urllib.request.Request(
            f"{url}/set/{key}",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):
            return True
    except:
        pass
    return False


def _json_load():
    try:
        if os.path.exists(_JSON_PATH):
            with open(_JSON_PATH, "r") as f:
                return json.load(f)
    except:
        pass
    return []


def _json_save(users):
    try:
        with open(_JSON_PATH, "w") as f:
            json.dump(users, f)
        return True
    except:
        return False


def _has_kv():
    return bool(os.environ.get("KV_REST_API_URL") and os.environ.get("KV_REST_API_TOKEN"))


def get_all_users():
    if _has_kv():
        users = _kv_get("users")
        return users if isinstance(users, list) else []
    return _json_load()


def save_users(users):
    if _has_kv():
        return _kv_set("users", users)
    return _json_save(users)


def find_user(login):
    for u in get_all_users():
        if u.get("login") == login:
            return u
    return None


def create_user(login, password):
    if not login or not password or find_user(login):
        return None
    users = get_all_users()
    users.append({
        "login": login,
        "password_hash": _hash_password(password),
        "period_days": 0,
        "activated_at": None,
        "expires_at": None,
        "status": "inactive",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None,
        "machine_id": None,
    })
    save_users(users)
    return True


def verify_user(login, password):
    user = find_user(login)
    if not user or user.get("password_hash") != _hash_password(password):
        return None
    return user


def set_user_period(login, days):
    users = get_all_users()
    now = datetime.now(timezone.utc)
    for u in users:
        if u["login"] == login:
            u["period_days"] = days
            u["activated_at"] = now.isoformat()
            u["expires_at"] = (now + timedelta(days=days)).isoformat()
            u["status"] = "active"
            save_users(users)
            return True
    return False


def revoke_user(login):
    users = get_all_users()
    for u in users:
        if u["login"] == login:
            u["status"] = "revoked"
            save_users(users)
            return True
    return False


def update_user_login(login, machine_id=None):
    users = get_all_users()
    for u in users:
        if u["login"] == login:
            u["last_login"] = datetime.now(timezone.utc).isoformat()
            if machine_id:
                u["machine_id"] = machine_id
            save_users(users)
            return True
    return False


def check_user_period(login):
    user = find_user(login)
    if not user:
        return {"active": False, "days_left": 0, "error": "user_not_found"}
    if user.get("status") == "revoked":
        return {"active": False, "days_left": 0, "error": "revoked"}
    if not user.get("expires_at"):
        return {"active": False, "days_left": 0, "error": "not_activated"}
    now = datetime.now(timezone.utc)
    expires = datetime.fromisoformat(user["expires_at"])
    if now > expires:
        users = get_all_users()
        for u in users:
            if u["login"] == login:
                u["status"] = "expired"
        save_users(users)
        return {"active": False, "days_left": 0, "error": "expired"}
    days_left = max(0, (expires - now).days)
    return {"active": True, "days_left": days_left, "expires_at": user["expires_at"], "period_days": user.get("period_days", 0)}


def is_admin(login, password):
    return login == ADMIN_LOGIN and password == ADMIN_PASSWORD
