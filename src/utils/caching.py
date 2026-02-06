"""
Caching utilities for Hallucination Hunter
"""

import hashlib
import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union
from functools import wraps
from dataclasses import dataclass

import joblib


T = TypeVar('T')


@dataclass
class CacheEntry:
    """Represents a cached item with metadata"""
    value: Any
    created_at: float
    ttl: Optional[int]
    key: str
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)


class CacheManager:
    """
    Manages caching for embeddings, model outputs, and intermediate results
    Supports both in-memory and disk-based caching
    """
    
    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        default_ttl: int = 3600,
        max_memory_items: int = 1000,
        enabled: bool = True
    ):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory for disk cache (None for memory-only)
            default_ttl: Default time-to-live in seconds
            max_memory_items: Maximum items in memory cache
            enabled: Whether caching is enabled
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.default_ttl = default_ttl
        self.max_memory_items = max_memory_items
        self.enabled = enabled
        
        # In-memory cache
        self._memory_cache: dict[str, CacheEntry] = {}
        
        # Create cache directory
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a unique cache key from arguments"""
        key_data = {
            "args": [str(a) for a in args],
            "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None
        
        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if not entry.is_expired:
                return entry.value
            else:
                del self._memory_cache[key]
        
        # Check disk cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                try:
                    entry = joblib.load(cache_file)
                    if not entry.is_expired:
                        # Also store in memory for faster access
                        self._add_to_memory(key, entry)
                        return entry.value
                    else:
                        cache_file.unlink()  # Delete expired file
                except Exception:
                    pass
        
        return None
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        persist: bool = True
    ) -> None:
        """
        Store item in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None for default)
            persist: Whether to persist to disk
        """
        if not self.enabled:
            return
        
        entry = CacheEntry(
            value=value,
            created_at=time.time(),
            ttl=ttl if ttl is not None else self.default_ttl,
            key=key
        )
        
        # Store in memory
        self._add_to_memory(key, entry)
        
        # Persist to disk
        if persist and self.cache_dir:
            cache_file = self.cache_dir / f"{key}.cache"
            try:
                joblib.dump(entry, cache_file)
            except Exception:
                pass  # Silent fail for disk caching
    
    def _add_to_memory(self, key: str, entry: CacheEntry) -> None:
        """Add entry to memory cache with LRU eviction"""
        if len(self._memory_cache) >= self.max_memory_items:
            # Remove oldest entry
            oldest_key = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k].created_at
            )
            del self._memory_cache[oldest_key]
        
        self._memory_cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """
        Delete item from cache
        
        Returns:
            True if item was deleted
        """
        deleted = False
        
        if key in self._memory_cache:
            del self._memory_cache[key]
            deleted = True
        
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                cache_file.unlink()
                deleted = True
        
        return deleted
    
    def clear(self, memory_only: bool = False) -> int:
        """
        Clear all cached items
        
        Args:
            memory_only: If True, only clear memory cache
        
        Returns:
            Number of items cleared
        """
        count = len(self._memory_cache)
        self._memory_cache.clear()
        
        if not memory_only and self.cache_dir:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                    count += 1
                except Exception:
                    pass
        
        return count
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache
        
        Returns:
            Number of entries removed
        """
        removed = 0
        
        # Clean memory cache
        expired_keys = [
            k for k, v in self._memory_cache.items() 
            if v.is_expired
        ]
        for key in expired_keys:
            del self._memory_cache[key]
            removed += 1
        
        # Clean disk cache
        if self.cache_dir:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    entry = joblib.load(cache_file)
                    if entry.is_expired:
                        cache_file.unlink()
                        removed += 1
                except Exception:
                    pass
        
        return removed
    
    def cached(
        self,
        ttl: Optional[int] = None,
        key_prefix: str = "",
        persist: bool = True
    ) -> Callable:
        """
        Decorator for caching function results
        
        Args:
            ttl: Time-to-live for cached results
            key_prefix: Prefix for cache keys
            persist: Whether to persist to disk
        
        Returns:
            Decorator function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                # Generate cache key
                base_key = self._generate_key(*args, **kwargs)
                key = f"{key_prefix}_{base_key}" if key_prefix else base_key
                
                # Try to get from cache
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value
                
                # Call function and cache result
                result = func(*args, **kwargs)
                self.set(key, result, ttl=ttl, persist=persist)
                
                return result
            
            return wrapper
        return decorator
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        memory_count = len(self._memory_cache)
        disk_count = 0
        disk_size = 0
        
        if self.cache_dir:
            cache_files = list(self.cache_dir.glob("*.cache"))
            disk_count = len(cache_files)
            disk_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "memory_items": memory_count,
            "disk_items": disk_count,
            "disk_size_bytes": disk_size,
            "disk_size_mb": disk_size / (1024 * 1024),
            "enabled": self.enabled,
            "max_memory_items": self.max_memory_items,
            "default_ttl": self.default_ttl
        }


# Global cache instance
_global_cache: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get global cache instance"""
    global _global_cache
    if _global_cache is None:
        from src.config.settings import get_settings
        settings = get_settings()
        _global_cache = CacheManager(
            cache_dir=settings.cache_dir,
            default_ttl=settings.cache_ttl,
            enabled=settings.cache_enabled
        )
    return _global_cache


def cached_embeddings(func: Callable) -> Callable:
    """Decorator for caching embedding computations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache = get_cache()
        key = cache._generate_key("embedding", *args, **kwargs)
        
        result = cache.get(key)
        if result is not None:
            return result
        
        result = func(*args, **kwargs)
        cache.set(key, result, persist=True)
        return result
    
    return wrapper


def cached_nli_results(func: Callable) -> Callable:
    """Decorator for caching NLI classification results"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache = get_cache()
        key = cache._generate_key("nli", *args, **kwargs)
        
        result = cache.get(key)
        if result is not None:
            return result
        
        result = func(*args, **kwargs)
        cache.set(key, result, persist=True)
        return result
    
    return wrapper
