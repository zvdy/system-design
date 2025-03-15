"""
Caching Strategies Implementation

This module demonstrates different caching strategies and replacement policies.
It includes implementations of LRU, LFU caches, and write-through/write-back policies.

ASCII Diagram:
```
┌─────────────────┐         ┌─────────────┐
│    Client       │         │   Cache     │
│   Requests      │◄───────►│   Layer     │
└─────────────────┘         └──────┬──────┘
                                   │
                                   ▼
                           ┌─────────────┐
                           │  Backend    │
                           │  Storage    │
                           └─────────────┘

Cache Policies:
┌──────────┐ ┌──────────┐ ┌──────────┐
│   LRU    │ │   LFU    │ │  FIFO    │
└──────────┘ └──────────┘ └──────────┘
```
"""

from typing import Dict, Any, Optional, List, Tuple
from collections import OrderedDict, defaultdict
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import threading

class CachePolicy(Enum):
    """Cache replacement policies"""
    LRU = "Least Recently Used"
    LFU = "Least Frequently Used"
    FIFO = "First In First Out"

class WritePolicy(Enum):
    """Cache write policies"""
    WRITE_THROUGH = "Write Through"
    WRITE_BACK = "Write Back"
    WRITE_AROUND = "Write Around"

@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    
    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class CacheBase(ABC):
    """Abstract base class for cache implementations"""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.stats = CacheStats()
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        pass
    
    @abstractmethod
    def put(self, key: str, value: Any) -> None:
        """Put item in cache"""
        pass
    
    @abstractmethod
    def remove(self, key: str) -> None:
        """Remove item from cache"""
        pass

class LRUCache(CacheBase):
    """Least Recently Used (LRU) cache implementation"""
    
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self.cache = OrderedDict()
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.stats.hits += 1
                return value
            self.stats.misses += 1
            return None
    
    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.capacity:
                # Remove least recently used item
                self.cache.popitem(last=False)
                self.stats.evictions += 1
            self.cache[key] = value

    def remove(self, key: str) -> None:
        with self._lock:
            if key in self.cache:
                self.cache.pop(key)

class LFUCache(CacheBase):
    """Least Frequently Used (LFU) cache implementation"""
    
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self.cache: Dict[str, Any] = {}
        self.frequencies: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self.cache:
                self.frequencies[key] += 1
                self.stats.hits += 1
                return self.cache[key]
            self.stats.misses += 1
            return None
    
    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self.cache:
                self.cache[key] = value
                self.frequencies[key] += 1
            elif len(self.cache) >= self.capacity:
                # Remove least frequently used item
                min_freq_key = min(self.frequencies.items(), key=lambda x: x[1])[0]
                self.cache.pop(min_freq_key)
                self.frequencies.pop(min_freq_key)
                self.stats.evictions += 1
                self.cache[key] = value
                self.frequencies[key] = 1
            else:
                self.cache[key] = value
                self.frequencies[key] = 1
    
    def remove(self, key: str) -> None:
        with self._lock:
            if key in self.cache:
                self.cache.pop(key)
                self.frequencies.pop(key)

class WriteBackCache:
    """Write-back cache implementation"""
    
    def __init__(self, capacity: int, storage_callback: callable):
        self.cache = LRUCache(capacity)
        self.storage_callback = storage_callback
        self.dirty: Dict[str, bool] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)
    
    def put(self, key: str, value: Any) -> None:
        with self._lock:
            self.cache.put(key, value)
            self.dirty[key] = True
    
    def flush(self) -> None:
        """Flush dirty entries to storage"""
        with self._lock:
            for key, value in self.cache.cache.items():
                if self.dirty.get(key, False):
                    self.storage_callback(key, value)
                    self.dirty[key] = False

class WriteThroughCache:
    """Write-through cache implementation"""
    
    def __init__(self, capacity: int, storage_callback: callable):
        self.cache = LRUCache(capacity)
        self.storage_callback = storage_callback
    
    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)
    
    def put(self, key: str, value: Any) -> None:
        self.storage_callback(key, value)  # Write to storage first
        self.cache.put(key, value)  # Then update cache

def demonstrate_caching():
    """Demonstrate different caching strategies"""
    
    # Simulated backend storage
    storage: Dict[str, Any] = {}
    def storage_callback(key: str, value: Any):
        storage[key] = value
        time.sleep(0.1)  # Simulate storage latency
    
    # LRU Cache Example
    print("LRU Cache Example:")
    print("-" * 50)
    
    lru_cache = LRUCache(2)
    lru_cache.put("A", 1)
    lru_cache.put("B", 2)
    print(f"Get A: {lru_cache.get('A')}")  # Returns 1
    lru_cache.put("C", 3)  # Evicts B
    print(f"Get B: {lru_cache.get('B')}")  # Returns None
    print(f"Cache stats - Hit ratio: {lru_cache.stats.hit_ratio:.2f}")
    
    # LFU Cache Example
    print("\nLFU Cache Example:")
    print("-" * 50)
    
    lfu_cache = LFUCache(2)
    lfu_cache.put("A", 1)
    lfu_cache.put("B", 2)
    lfu_cache.get("A")  # Frequency of A: 2
    lfu_cache.get("A")  # Frequency of A: 3
    lfu_cache.put("C", 3)  # Evicts B (lowest frequency)
    print(f"Get A: {lfu_cache.get('A')}")  # Returns 1
    print(f"Get B: {lfu_cache.get('B')}")  # Returns None
    print(f"Get C: {lfu_cache.get('C')}")  # Returns 3
    
    # Write-through Cache Example
    print("\nWrite-through Cache Example:")
    print("-" * 50)
    
    write_through = WriteThroughCache(2, storage_callback)
    write_through.put("X", 10)  # Immediately writes to storage
    print(f"Storage X: {storage.get('X')}")  # Returns 10
    print(f"Cache X: {write_through.get('X')}")  # Returns 10
    
    # Write-back Cache Example
    print("\nWrite-back Cache Example:")
    print("-" * 50)
    
    storage.clear()
    write_back = WriteBackCache(2, storage_callback)
    write_back.put("Y", 20)  # Only writes to cache
    print(f"Storage Y (before flush): {storage.get('Y')}")  # Returns None
    write_back.flush()  # Write to storage
    print(f"Storage Y (after flush): {storage.get('Y')}")  # Returns 20

if __name__ == "__main__":
    print("Running Caching Strategies Example")
    demonstrate_caching() 