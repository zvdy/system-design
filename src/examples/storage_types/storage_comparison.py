"""
Storage Types Comparison

This module demonstrates different storage types and their characteristics.
It includes examples of key-value stores, document stores, and time-series databases.

ASCII Diagram:
```
┌────────────────────────────────────┐
│           Storage Types            │
├──────────────┬──────────┬─────────┤
│  Key-Value   │ Document │  Time-  │
│    Store     │  Store   │ Series  │
├──────────────┼──────────┼─────────┤
│ Fast Lookup  │ Flexible │ Time-   │
│ Simple Model │ Schema   │ Based   │
└──────────────┴──────────┴─────────┘
```
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import time
from datetime import datetime, timedelta
import bisect
from collections import defaultdict
import threading
import random

@dataclass
class TimeSeriesPoint:
    """Represents a point in time series data"""
    timestamp: datetime
    value: float
    tags: Dict[str, str]

class KeyValueStore:
    """Simple in-memory key-value store"""
    
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def put(self, key: str, value: Any) -> bool:
        """Store a value"""
        with self._lock:
            self._store[key] = value
            return True
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value"""
        with self._lock:
            return self._store.get(key)
    
    def delete(self, key: str) -> bool:
        """Delete a value"""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False
    
    def scan(self, prefix: str) -> List[tuple]:
        """Scan keys with prefix"""
        with self._lock:
            return [(k, v) for k, v in self._store.items() if k.startswith(prefix)]

class DocumentStore:
    """Simple in-memory document store with basic querying"""
    
    def __init__(self):
        self._store: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def insert(self, collection: str, document: Dict) -> str:
        """Insert a document"""
        with self._lock:
            if collection not in self._store:
                self._store[collection] = {}
            
            # Generate document ID if not provided
            if '_id' not in document:
                document['_id'] = str(time.time())
            
            self._store[collection][document['_id']] = document
            return document['_id']
    
    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        """Find one document matching query"""
        with self._lock:
            if collection not in self._store:
                return None
            
            for doc in self._store[collection].values():
                if self._matches(doc, query):
                    return doc.copy()
            
            return None
    
    def find(self, collection: str, query: Dict) -> List[Dict]:
        """Find all documents matching query"""
        with self._lock:
            if collection not in self._store:
                return []
            
            return [doc.copy() for doc in self._store[collection].values()
                   if self._matches(doc, query)]
    
    def _matches(self, document: Dict, query: Dict) -> bool:
        """Check if document matches query"""
        for key, value in query.items():
            if key not in document:
                return False
            if isinstance(value, dict):
                # Handle operators
                for op, op_value in value.items():
                    if op == '$gt':
                        if not document[key] > op_value:
                            return False
                    elif op == '$lt':
                        if not document[key] < op_value:
                            return False
                    elif op == '$in':
                        if document[key] not in op_value:
                            return False
            elif document[key] != value:
                return False
        return True

class TimeSeriesDB:
    """Simple in-memory time series database"""
    
    def __init__(self):
        self._series: Dict[str, List[TimeSeriesPoint]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def insert(self, series: str, point: TimeSeriesPoint):
        """Insert a data point"""
        with self._lock:
            bisect.insort(self._series[series], point,
                         key=lambda x: x.timestamp)
    
    def query_range(self, series: str, start: datetime,
                   end: datetime) -> List[TimeSeriesPoint]:
        """Query points within time range"""
        with self._lock:
            if series not in self._series:
                return []
            
            points = self._series[series]
            start_idx = bisect.bisect_left(points, TimeSeriesPoint(start, 0, {}),
                                         key=lambda x: x.timestamp)
            end_idx = bisect.bisect_right(points, TimeSeriesPoint(end, 0, {}),
                                        key=lambda x: x.timestamp)
            
            return points[start_idx:end_idx]
    
    def aggregate(self, series: str, start: datetime, end: datetime,
                 window: timedelta) -> List[tuple]:
        """Aggregate data points by time window"""
        points = self.query_range(series, start, end)
        if not points:
            return []
        
        result = []
        current_window = start
        window_points = []
        
        for point in points:
            while point.timestamp >= current_window + window:
                if window_points:
                    avg_value = sum(p.value for p in window_points) / len(window_points)
                    result.append((current_window, avg_value))
                window_points = []
                current_window += window
            
            window_points.append(point)
        
        if window_points:
            avg_value = sum(p.value for p in window_points) / len(window_points)
            result.append((current_window, avg_value))
        
        return result

def demonstrate_storage_types():
    """Demonstrate different storage types"""
    # Key-Value Store Example
    print("Key-Value Store Example:")
    print("-" * 50)
    
    kv_store = KeyValueStore()
    kv_store.put("user:1", {"name": "Alice", "age": 30})
    kv_store.put("user:2", {"name": "Bob", "age": 25})
    kv_store.put("user:3", {"name": "Charlie", "age": 35})
    
    print("Scan results for 'user:':")
    for key, value in kv_store.scan("user:"):
        print(f"{key}: {value}")
    
    # Document Store Example
    print("\nDocument Store Example:")
    print("-" * 50)
    
    doc_store = DocumentStore()
    
    # Insert documents
    doc_store.insert("users", {
        "name": "Alice",
        "age": 30,
        "interests": ["reading", "hiking"]
    })
    doc_store.insert("users", {
        "name": "Bob",
        "age": 25,
        "interests": ["gaming", "music"]
    })
    
    # Query documents
    print("\nFind users age > 27:")
    results = doc_store.find("users", {"age": {"$gt": 27}})
    for doc in results:
        print(doc)
    
    # Time Series DB Example
    print("\nTime Series DB Example:")
    print("-" * 50)
    
    ts_db = TimeSeriesDB()
    
    # Generate sample data
    start_time = datetime.now()
    for i in range(60):
        point = TimeSeriesPoint(
            timestamp=start_time + timedelta(minutes=i),
            value=random.uniform(20, 30),  # Temperature data
            tags={"sensor": "temp_1", "location": "room_1"}
        )
        ts_db.insert("temperature", point)
    
    # Query last 30 minutes
    end_time = start_time + timedelta(minutes=59)
    query_start = end_time - timedelta(minutes=30)
    
    print("\nLast 30 minutes aggregated by 10-minute windows:")
    aggregates = ts_db.aggregate(
        "temperature",
        query_start,
        end_time,
        timedelta(minutes=10)
    )
    
    for window_start, avg_value in aggregates:
        print(f"Window {window_start.strftime('%H:%M')}: {avg_value:.2f}°C")

if __name__ == "__main__":
    print("Running Storage Types Example")
    demonstrate_storage_types() 