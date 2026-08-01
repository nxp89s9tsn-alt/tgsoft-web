"""
Shared storage — uses Vercel KV or JSON file fallback.
"""
import json
import os
import hashlib
import time
from datetime import datetime, timezone, timedelta

ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "tgsoft_admin_2024")


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _get_kv_url():
    return os.environ.get("KV_REST_API_URL", "")


def _get_kv_token():
    return os.environ.get("KV_REST_API_TOKEN", "")


def _kv_get(key: str):
    url = _get_kv_url()
    token = _get_kv_token()
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
    except Exception:
        pass
    return None


def _kv_set(key: str, value):
    url = _get_kv_url()
    token = _get_kv_token()
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
        with urllib.request.urlopen(req, timeout=5) as resp:
            return True
    except Exception:
        pass
    return False


def _kv_keys(pattern: str = "*"):
    url = _get_kv_url()
    token = _get_kv_token()
    if not url or not token:
        return []
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{url}/keys/{pattern}",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("result", [])
    except Exception:
        return []


# ===== User operations =====

def get_all_users() -> list:
    """Returns all users from KV."""
    users = _kv_get("users")
    if users is None:
        return []
    if isinstance(users, list):
        return users
    return []


def save_users(users: list) -> bool:
    return _kv_set("users", users)


def find_user(login: str) -> dict | None:
    users = get_all_users()
    for u in users:
        if u.get("login") == login:
            return u
    return None


def create_user(login: str, password: str) -> dict | None:
    if not login or not password:
        return None
    if find_user(login):
        return None
    users = get_all_users()
    user = {
        "login": login,
        "password_hash": _hash_password(password),
        "period_days": 0,
        "activated_at": None,
        "expires_at": None,
        "status": "inactive",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None,
        "machine_id": None,
    }
    users.append(user)
    save_users(users)
    return user


def verify_user(login: str, password: str) -> dict | None:
    user = find_user(login)
    if not user:
        return None
    if user.get("password_hash") != _hash_password(password):
        return None
    return user


def set_user_period(login: str, days: int) -> bool:
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


def revoke_user(login: str) -> bool:
    users = get_all_users()
    for u in users:
        if u["login"] == login:
            u["status"] = "revoked"
            save_users(users)
            return True
    return False


def update_user_login(login: str, machine_id: str = None) -> bool:
    users = get_all_users()
    for u in users:
        if u["login"] == login:
            u["last_login"] = datetime.now(timezone.utc).isoformat()
            if machine_id:
                u["machine_id"] = machine_id
            save_users(users)
            return True
    return False


def check_user_period(login: str) -> dict:
    """Returns {active, days_left, expires_at}."""
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
        # Auto-expire
        users = get_all_users()
        for u in users:
            if u["login"] == login:
                u["status"] = "expired"
                save_users(users)
        return {"active": False, "days_left": 0, "error": "expired"}

    days_left = max(0, (expires - now).days)
    return {
        "active": True,
        "days_left": days_left,
        "expires_at": user["expires_at"],
        "period_days": user.get("period_days", 0),
    }


def is_admin(login: str, password: str) -> bool:
    return login == ADMIN_LOGIN and password == ADMIN_PASSWORD
