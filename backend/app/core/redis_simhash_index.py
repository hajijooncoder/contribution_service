"""
Redis-based SimHash Index for Near-Duplicate Detection
Provides O(1) candidate lookup instead of O(N) full table scan.
"""

import hashlib
import logging
from typing import List, Optional, Set
from app.config import settings

logger = logging.getLogger(__name__)

SIMHASH_CHUNK_SIZE = 16  # 64-bit fingerprint split into 4 chunks of 16 bits
SIMHASH_NUM_CHUNKS = 4
SIMHASH_KEY_PREFIX = "simhash:idx"


class RedisSimHashIndex:
    """
    Redis-backed SimHash index using multi-index chunking.
    
    Algorithm:
    - Split 64-bit SimHash into 4 chunks of 16 bits each
    - Store submission_id in sorted sets for each chunk value
    - For lookup: query all 4 chunks, union candidates, compute exact similarity
    - This reduces candidate set from O(N) to O(1) average
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._enabled = redis_client is not None
    
    @property
    def enabled(self) -> bool:
        return self._enabled and self.redis is not None
    
    def _get_chunk_keys(self, fingerprint: str) -> List[str]:
        """Generate Redis keys for each 16-bit chunk of the fingerprint."""
        keys = []
        for i in range(SIMHASH_NUM_CHUNKS):
            start = i * SIMHASH_CHUNK_SIZE
            end = start + SIMHASH_CHUNK_SIZE
            chunk = fingerprint[start:end]
            keys.append(f"{SIMHASH_KEY_PREFIX}:{i}:{chunk}")
        return keys
    
    def add(self, submission_id: str, fingerprint: str) -> bool:
        """Add a submission's fingerprint to the index."""
        if not self.enabled:
            return False
        
        try:
            pipe = self.redis.pipeline()
            for key in self._get_chunk_keys(fingerprint):
                pipe.zadd(key, {submission_id: 1})
            pipe.execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to add to SimHash index: {e}")
            return False
    
    def remove(self, submission_id: str, fingerprint: str) -> bool:
        """Remove a submission's fingerprint from the index."""
        if not self.enabled:
            return False
        
        try:
            pipe = self.redis.pipeline()
            for key in self._get_chunk_keys(fingerprint):
                pipe.zrem(key, submission_id)
            pipe.execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to remove from SimHash index: {e}")
            return False
    
    def find_candidates(self, fingerprint: str, max_candidates: int = 100) -> Set[str]:
        """
        Find candidate submission IDs that share at least one chunk.
        Returns a set of candidate IDs for exact similarity verification.
        """
        if not self.enabled:
            return set()
        
        try:
            candidates = set()
            for key in self._get_chunk_keys(fingerprint):
                # Get all members from each chunk's sorted set
                members = self.redis.zrange(key, 0, -1)
                candidates.update(members)
                
                # Early exit if we have enough candidates
                if len(candidates) >= max_candidates * 2:
                    break
            
            return candidates
        except Exception as e:
            logger.warning(f"Failed to query SimHash index: {e}")
            return set()
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = {"enabled": True, "chunks": {}}
            for i in range(SIMHASH_NUM_CHUNKS):
                pattern = f"{SIMHASH_KEY_PREFIX}:{i}:*"
                keys = self.redis.keys(pattern)
                info["chunks"][f"chunk_{i}"] = len(keys)
            return info
        except Exception:
            return {"enabled": True, "error": "Failed to get stats"}


# Global instance
_simhash_index: Optional[RedisSimHashIndex] = None


def get_simhash_index() -> RedisSimHashIndex:
    global _simhash_index
    if _simhash_index is None:
        try:
            if settings.REDIS_URL:
                import redis
                client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                _simhash_index = RedisSimHashIndex(client)
            else:
                _simhash_index = RedisSimHashIndex(None)
        except Exception as e:
            logger.warning(f"Failed to initialize Redis SimHash index: {e}")
            _simhash_index = RedisSimHashIndex(None)
    return _simhash_index