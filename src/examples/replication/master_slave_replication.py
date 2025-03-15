"""
Master-Slave Replication Example

This module demonstrates a simple master-slave replication pattern using Python.
It simulates a master database with multiple read replicas.

ASCII Diagram:
```
                  ┌──────────┐
            ┌────►│ Replica 1│
            │     └──────────┘
┌──────────┐│     ┌──────────┐
│  Master  ├┼────►│ Replica 2│
└──────────┘│     └──────────┘
            │     ┌──────────┐
            └────►│ Replica 3│
                  └──────────┘
```
"""

import threading
import time
import random
import queue
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class DataRecord:
    """Represents a data record in our database"""
    key: str
    value: str
    timestamp: float
    version: int

class ReplicationLog:
    """Represents the replication log that tracks changes"""
    def __init__(self):
        self.entries: List[DataRecord] = []
        self._lock = threading.Lock()
    
    def append(self, record: DataRecord):
        """Add a new record to the replication log"""
        with self._lock:
            self.entries.append(record)
    
    def get_entries_after(self, timestamp: float) -> List[DataRecord]:
        """Get all entries after a specific timestamp"""
        with self._lock:
            return [entry for entry in self.entries if entry.timestamp > timestamp]

class Database:
    """Base class for both master and replica databases"""
    def __init__(self, name: str):
        self.name = name
        self.data: Dict[str, DataRecord] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[str]:
        """Read a value from the database"""
        with self._lock:
            record = self.data.get(key)
            return record.value if record else None
    
    def _set(self, record: DataRecord):
        """Internal method to set a value"""
        with self._lock:
            self.data[record.key] = record

class MasterDatabase(Database):
    """Master database that handles writes and replication"""
    def __init__(self):
        super().__init__("Master")
        self.replication_log = ReplicationLog()
        self.replicas: List[ReplicaDatabase] = []
        self.version = 0
    
    def set(self, key: str, value: str) -> DataRecord:
        """Write a value to the master database"""
        self.version += 1
        record = DataRecord(
            key=key,
            value=value,
            timestamp=time.time(),
            version=self.version
        )
        
        # Update master
        self._set(record)
        
        # Add to replication log
        self.replication_log.append(record)
        
        # Notify replicas
        for replica in self.replicas:
            replica.notify_change()
        
        return record
    
    def add_replica(self, replica: 'ReplicaDatabase'):
        """Add a new replica to the master"""
        self.replicas.append(replica)
        replica.set_master(self)

class ReplicaDatabase(Database):
    """Replica database that handles reads and replication from master"""
    def __init__(self, name: str):
        super().__init__(name)
        self.master: Optional[MasterDatabase] = None
        self.last_replicated: float = 0
        self.replication_queue = queue.Queue()
        self.replication_thread = threading.Thread(target=self._replication_worker)
        self.replication_thread.daemon = True
        self.replication_thread.start()
    
    def set_master(self, master: MasterDatabase):
        """Set the master database for this replica"""
        self.master = master
    
    def notify_change(self):
        """Notify the replica that there are changes to replicate"""
        self.replication_queue.put(True)
    
    def _replication_worker(self):
        """Background worker that handles replication from master"""
        while True:
            # Wait for notification
            self.replication_queue.get()
            
            if self.master:
                # Get new changes from master's replication log
                new_records = self.master.replication_log.get_entries_after(self.last_replicated)
                
                # Apply changes
                for record in new_records:
                    self._set(record)
                    self.last_replicated = record.timestamp
                
                print(f"{self.name}: Replicated {len(new_records)} records")
            
            # Mark task as done
            self.replication_queue.task_done()

def simulate_traffic(master: MasterDatabase, duration: int = 10):
    """Simulate database traffic with writes to master and reads from replicas"""
    start_time = time.time()
    keys = ["user_1", "user_2", "user_3", "user_4", "user_5"]
    
    while time.time() - start_time < duration:
        # Simulate write to master
        key = random.choice(keys)
        value = f"value_{random.randint(1, 100)}"
        master.set(key, value)
        print(f"Master: Write {key}={value}")
        
        # Simulate read from replicas
        for replica in master.replicas:
            key = random.choice(keys)
            value = replica.get(key)
            print(f"{replica.name}: Read {key}={value}")
        
        time.sleep(0.5)

if __name__ == "__main__":
    # Create master database
    master = MasterDatabase()
    
    # Create replicas
    replicas = [
        ReplicaDatabase("Replica-1"),
        ReplicaDatabase("Replica-2"),
        ReplicaDatabase("Replica-3")
    ]
    
    # Add replicas to master
    for replica in replicas:
        master.add_replica(replica)
    
    print("Starting replication simulation...")
    print("-" * 50)
    
    # Simulate traffic
    simulate_traffic(master)
    
    print("-" * 50)
    print("Simulation complete") 