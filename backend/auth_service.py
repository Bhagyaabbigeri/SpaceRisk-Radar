import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Dict, Optional

from flask import g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

try:
    import jwt
except Exception:  # pragma: no cover - optional dependency fallback
    jwt = None


DATA_DIR = os.path.dirname(__file__)
DB_FILE = os.environ.get("CRV_AUTH_DB", os.path.join(DATA_DIR, "app_data.db"))
JWT_SECRET = os.environ.get("CRV_JWT_SECRET", "dev-change-me-collision-risk-visualizer")
JWT_ISSUER = "collision-risk-visualizer"
TOKEN_TTL_SECONDS = int(os.environ.get("CRV_TOKEN_TTL_SECONDS", str(8 * 60 * 60)))


class AuthService:
    """Small SQLite-backed auth/profile store.

    This keeps infrastructure self-contained for local deployment while exposing
    clean seams for replacing SQLite with Postgres later.
    """

    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self._memory_conn = None
        self.signer = URLSafeTimedSerializer(JWT_SECRET, salt="crv-auth")
        try:
            self.init_db()
        except sqlite3.Error:
            # Keep the app available even when the local filesystem rejects
            # SQLite writes. Production should set CRV_AUTH_DB to reliable
            # storage or replace this service with a managed database.
            self.db_file = ":memory:"
            self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_conn.row_factory = sqlite3.Row
            self.init_db()

    def _connect(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    display_name TEXT,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS preferences (
                    user_id INTEGER PRIMARY KEY,
                    preferences_json TEXT NOT NULL,
                    alert_threshold_km REAL NOT NULL DEFAULT 50.0,
                    email_alerts_enabled INTEGER NOT NULL DEFAULT 0,
                    webhook_url TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS watched_satellites (
                    user_id INTEGER NOT NULL,
                    satellite_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(user_id, satellite_name),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )

    def create_user(self, email: str, password: str, display_name: str = "", role: str = "user") -> Dict[str, Any]:
        email = (email or "").strip().lower()
        if not email or "@" not in email:
            raise ValueError("valid email is required")
        if len(password or "") < 8:
            raise ValueError("password must be at least 8 characters")
        role = role if role in {"admin", "user"} else "user"
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            try:
                cur = conn.execute(
                    """
                    INSERT INTO users (email, password_hash, display_name, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (email, generate_password_hash(password), display_name or email.split("@")[0], role, now, now),
                )
                user_id = cur.lastrowid
                conn.execute(
                    "INSERT INTO preferences (user_id, preferences_json) VALUES (?, ?)",
                    (user_id, json.dumps(default_preferences())),
                )
            except sqlite3.IntegrityError:
                raise ValueError("email already registered")

        return self.get_user(user_id)

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.get_user_by_email((email or "").strip().lower())
        if not user or not check_password_hash(user["password_hash"], password or ""):
            return None
        return self.public_user(user)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            return dict(row) if row else None

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return self.public_user(dict(row)) if row else None

    def public_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("display_name"),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at"),
        }

    def issue_token(self, user: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=TOKEN_TTL_SECONDS)).timestamp()),
            "iss": JWT_ISSUER,
            "jti": secrets.token_urlsafe(12),
        }
        if jwt:
            return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        return self.signer.dumps(payload)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            if jwt:
                payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], issuer=JWT_ISSUER)
            else:
                payload = self.signer.loads(token, max_age=TOKEN_TTL_SECONDS)
            return self.get_user(int(payload["sub"]))
        except (BadSignature, SignatureExpired, KeyError, ValueError):
            return None
        except Exception:
            return None

    def update_profile(self, user_id: int, display_name: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET display_name = ?, updated_at = ? WHERE id = ?",
                ((display_name or "").strip(), now, user_id),
            )
        return self.get_user(user_id)

    def get_preferences(self, user_id: int) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM preferences WHERE user_id = ?", (user_id,)).fetchone()
            watched = [
                r["satellite_name"]
                for r in conn.execute(
                    "SELECT satellite_name FROM watched_satellites WHERE user_id = ? ORDER BY satellite_name",
                    (user_id,),
                ).fetchall()
            ]
        if not row:
            prefs = default_preferences()
            alert_threshold = 50.0
            email_enabled = False
            webhook_url = None
        else:
            prefs = json.loads(row["preferences_json"])
            alert_threshold = row["alert_threshold_km"]
            email_enabled = bool(row["email_alerts_enabled"])
            webhook_url = row["webhook_url"]
        return {
            "preferences": prefs,
            "watched_satellites": watched,
            "alert_threshold_km": alert_threshold,
            "email_alerts_enabled": email_enabled,
            "webhook_url": webhook_url,
        }

    def update_preferences(self, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_preferences(user_id)
        prefs = {**current["preferences"], **(payload.get("preferences") or {})}
        threshold = float(payload.get("alert_threshold_km", current["alert_threshold_km"]))
        threshold = max(1.0, min(5000.0, threshold))
        email_enabled = 1 if payload.get("email_alerts_enabled", current["email_alerts_enabled"]) else 0
        webhook_url = payload.get("webhook_url", current["webhook_url"])

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO preferences (user_id, preferences_json, alert_threshold_km, email_alerts_enabled, webhook_url)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    preferences_json=excluded.preferences_json,
                    alert_threshold_km=excluded.alert_threshold_km,
                    email_alerts_enabled=excluded.email_alerts_enabled,
                    webhook_url=excluded.webhook_url
                """,
                (user_id, json.dumps(prefs), threshold, email_enabled, webhook_url),
            )
        return self.get_preferences(user_id)

    def add_watched_satellite(self, user_id: int, satellite_name: str) -> Dict[str, Any]:
        name = (satellite_name or "").strip()
        if not name:
            raise ValueError("satellite_name is required")
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO watched_satellites (user_id, satellite_name, created_at) VALUES (?, ?, ?)",
                (user_id, name, datetime.now(timezone.utc).isoformat()),
            )
        return self.get_preferences(user_id)

    def remove_watched_satellite(self, user_id: int, satellite_name: str) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM watched_satellites WHERE user_id = ? AND satellite_name = ?",
                (user_id, satellite_name),
            )
        return self.get_preferences(user_id)

    def users_for_alerts(self) -> list[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT u.id, u.email, u.display_name, p.alert_threshold_km,
                       p.email_alerts_enabled, p.webhook_url
                FROM users u
                JOIN preferences p ON p.user_id = u.id
                WHERE p.email_alerts_enabled = 1 OR p.webhook_url IS NOT NULL
                """
            ).fetchall()
        return [dict(row) for row in rows]


def default_preferences() -> Dict[str, Any]:
    return {
        "theme": "dark",
        "default_orbit_filter": "ALL",
        "show_heatmap": True,
        "show_ground_visibility": True,
        "show_debris_clouds": True,
    }


auth_service = AuthService()


def current_user_from_request() -> Optional[Dict[str, Any]]:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return auth_service.verify_token(header.split(" ", 1)[1].strip())


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user_from_request()
        if not user:
            return jsonify({"error": "authentication required"}), 401
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def require_role(role: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user_from_request()
            if not user:
                return jsonify({"error": "authentication required"}), 401
            if user.get("role") != role:
                return jsonify({"error": "insufficient privileges"}), 403
            g.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator
