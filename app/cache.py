import time
import json
import logging
from typing import Any, Optional
import redis
from app.config import settings

logger = logging.getLogger("eve_healthcare")


class CacheService:
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        self._in_memory_cache: dict[str, tuple[Any, float]] = {}
        self._is_redis_available = False
        self._init_redis()

    def _init_redis(self):
        try:
            client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1)
            client.ping()
            self._redis_client = client
            self._is_redis_available = True
            logger.info("Connected to Redis cache successfully")
        except Exception as e:
            self._is_redis_available = False
            self._redis_client = None
            logger.info(f"Redis not available, using in-memory TTL cache fallback ({str(e)})")

    @property
    def is_redis(self) -> bool:
        return self._is_redis_available

    def get(self, key: str) -> Optional[Any]:
        if self._is_redis_available and self._redis_client:
            try:
                val = self._redis_client.get(key)
                return json.loads(val) if val else None
            except Exception:
                pass
        
        # In-memory fallback
        if key in self._in_memory_cache:
            val, expiry = self._in_memory_cache[key]
            if time.time() < expiry:
                return val
            else:
                del self._in_memory_cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        ttl = ttl or settings.CACHE_TTL_SECONDS
        try:
            json_val = json.dumps(value, default=str)
        except Exception:
            json_val = str(value)

        if self._is_redis_available and self._redis_client:
            try:
                self._redis_client.set(key, json_val, ex=ttl)
                return True
            except Exception:
                pass
        
        # In-memory fallback
        self._in_memory_cache[key] = (value, time.time() + ttl)
        return True

    def delete(self, key: str) -> bool:
        if self._is_redis_available and self._redis_client:
            try:
                self._redis_client.delete(key)
            except Exception:
                pass
        self._in_memory_cache.pop(key, None)
        return True

    def delete_prefix(self, prefix: str) -> bool:
        if self._is_redis_available and self._redis_client:
            try:
                keys = self._redis_client.keys(f"{prefix}*")
                if keys:
                    self._redis_client.delete(*keys)
            except Exception:
                pass
        
        # In-memory fallback
        keys_to_del = [k for k in self._in_memory_cache if k.startswith(prefix)]
        for k in keys_to_del:
            del self._in_memory_cache[k]
        return True

    def clear(self):
        if self._is_redis_available and self._redis_client:
            try:
                self._redis_client.flushdb()
            except Exception:
                pass
        self._in_memory_cache.clear()


cache = CacheService()
