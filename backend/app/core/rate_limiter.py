import time
import logging
from collections import defaultdict
from threading import Lock
from typing import Dict, List
from fastapi import Request
from app.config import settings

logger = logging.getLogger(__name__)

def get_client_ip(request: Request) -> str:
    direct_client = request.client.host if request.client else "unknown"
    
    if direct_client in settings.TRUSTED_PROXIES:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
            if client_ip:
                return client_ip
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
    
    return direct_client

class SlidingWindowRateLimiter:
    def __init__(self, default_limit: int = 20, default_window_seconds: int = 60):
        self.default_limit = default_limit
        self.default_window_seconds = default_window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.lock = Lock()
        self._redis_client = None
        
        if settings.REDIS_URL:
            try:
                import redis
                self._redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            except ImportError:
                logger.warning("redis package not installed, using in-memory rate limiter")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client for rate limiter: {e}")

    def is_allowed(self, key: str, limit: int = None, window_seconds: int = None) -> bool:
        max_allowed = limit if limit is not None else self.default_limit
        window = window_seconds if window_seconds is not None else self.default_window_seconds
        now = time.time()

        if self._redis_client:
            try:
                pipe = self._redis_client.pipeline()
                redis_key = f"rl:{key}"
                clear_before = now - window
                pipe.zremrangebyscore(redis_key, 0, clear_before)
                pipe.zcard(redis_key)
                pipe.zadd(redis_key, {str(now): now})
                pipe.expire(redis_key, window + 10)
                _, current_count, _, _ = pipe.execute()
                return current_count < max_allowed
            except Exception as e:
                logger.warning(f"Redis rate limiter error, falling back to in-memory: {e}")

        with self.lock:
            timestamps = self.requests[key]
            valid_timestamps = [ts for ts in timestamps if now - ts < window]
            self.requests[key] = valid_timestamps

            if len(valid_timestamps) >= max_allowed:
                return False

            self.requests[key].append(now)
            return True

    def reset(self, key: str = None):
        with self.lock:
            if key:
                self.requests.pop(key, None)
            else:
                self.requests.clear()
        if self._redis_client:
            try:
                if key:
                    self._redis_client.delete(f"rl:{key}")
                else:
                    keys = self._redis_client.keys("rl:*")
                    if keys:
                        self._redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Failed to reset Redis rate limiter keys: {e}")

global_rate_limiter = SlidingWindowRateLimiter()