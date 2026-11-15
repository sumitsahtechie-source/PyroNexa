"""PyroNexa 26 - Cache Service

Provides file-backed and memory-accelerated caching for NASA FIRMS queries
and heavy analytics computations to respect NASA rate limits and accelerate
dashboard response times.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Optional, Dict

from backend.config import Config


class CacheService:
    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: int = 3600):
        self.cache_dir = cache_dir or Config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self.stats = {"hits": 0, "misses": 0, "writes": 0}

    def _generate_key(self, namespace: str, params: Dict[str, Any]) -> str:
        """Create a deterministic hash key from namespace and parameter dictionary."""
        sorted_str = json.dumps(params, sort_keys=True, default=str)
        raw = f"{namespace}:{sorted_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, namespace: str, params: Dict[str, Any]) -> Optional[Any]:
        """Retrieve item from memory or disk cache if not expired."""
        key = self._generate_key(namespace, params)

        # Check in-memory cache first
        now = time.time()
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if now < entry["expires_at"]:
                self.stats["hits"] += 1
                return entry["data"]
            else:
                del self._memory_cache[key]

        # Check disk cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    disk_entry = json.load(f)
                if now < disk_entry.get("expires_at", 0):
                    # Populate memory cache
                    self._memory_cache[key] = disk_entry
                    self.stats["hits"] += 1
                    return disk_entry["data"]
                else:
                    # Expired, clean up
                    cache_file.unlink(missing_ok=True)
            except Exception:
                cache_file.unlink(missing_ok=True)

        self.stats["misses"] += 1
        return None

    def set(self, namespace: str, params: Dict[str, Any], data: Any, ttl: Optional[int] = None) -> None:
        """Store item in both memory and disk cache with TTL."""
        key = self._generate_key(namespace, params)
        ttl_val = self.ttl_seconds if ttl is None else ttl
        expires_at = time.time() + ttl_val

        entry = {
            "key": key,
            "namespace": namespace,
            "created_at": time.time(),
            "expires_at": expires_at,
            "data": data
        }

        self._memory_cache[key] = entry

        # Save to disk
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, default=str)
            self.stats["writes"] += 1
        except Exception:
            pass

    def clear(self) -> int:
        """Clear all cached entries from memory and disk. Returns count cleared."""
        self._memory_cache.clear()
        count = 0
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
                count += 1
            except Exception:
                pass
        return count

    def get_info(self) -> Dict[str, Any]:
        """Return diagnostic metrics about cache state."""
        disk_files = list(self.cache_dir.glob("*.json"))
        return {
            "memory_entries": len(self._memory_cache),
            "disk_files": len(disk_files),
            "ttl_seconds": self.ttl_seconds,
            "stats": self.stats
        }


# Singleton instance
cache_service = CacheService()
