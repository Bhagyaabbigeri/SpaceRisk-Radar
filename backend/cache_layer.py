import json
import logging
import os
import time
from typing import Any, Optional


logger = logging.getLogger(__name__)


class CacheLayer:
    """Redis-backed cache with in-memory fallback.

    The fallback keeps local development and offline runs functional while
    allowing Redis to be dropped into production with no route changes.
    """

    def __init__(self):
        self.memory: dict[str, tuple[float, str]] = {}
        self.redis = None
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis
            self.redis = redis.Redis.from_url(self.redis_url, socket_connect_timeout=1, socket_timeout=1)
            self.redis.ping()
            logger.info("Redis cache connected.")
        except Exception as exc:
            self.redis = None
            logger.warning(f"Redis unavailable; using in-memory cache fallback: {exc}")

    def get_json(self, key: str) -> Optional[Any]:
        if self.redis:
            try:
                raw = self.redis.get(key)
                return json.loads(raw) if raw else None
            except Exception as exc:
                logger.warning(f"Redis get failed for {key}: {exc}")

        item = self.memory.get(key)
        if not item:
            return None
        expires_at, raw = item
        if expires_at < time.time():
            self.memory.pop(key, None)
            return None
        return json.loads(raw)

    def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        raw = json.dumps(value)
        if self.redis:
            try:
                self.redis.setex(key, ttl_seconds, raw)
                return
            except Exception as exc:
                logger.warning(f"Redis set failed for {key}: {exc}")
        self.memory[key] = (time.time() + ttl_seconds, raw)

    def get_text(self, key: str) -> Optional[str]:
        value = self.get_json(key)
        return value if isinstance(value, str) else None

    def set_text(self, key: str, value: str, ttl_seconds: int = 300) -> None:
        self.set_json(key, value, ttl_seconds)

    def status(self) -> dict[str, Any]:
        return {
            "backend": "redis" if self.redis else "memory",
            "redis_url": self.redis_url if self.redis else None,
            "memory_keys": len(self.memory),
        }


cache_layer = CacheLayer()
