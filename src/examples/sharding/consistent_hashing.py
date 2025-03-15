"""
Consistent Hashing Implementation

This module demonstrates consistent hashing for distributing data across multiple shards.
It includes virtual nodes for better distribution and supports dynamic addition/removal of nodes.

ASCII Diagram:
```
     ┌──────────────────Hash Ring─────────────────┐
     │                                            │
     │    ┌─Node 1──┐         ┌─Node 2──┐        │
     │    │ Virtual │         │ Virtual │        │
     │    │ Node 1.1│         │ Node 2.1│        │
     │    └─────────┘         └─────────┘        │
     │                                           │
     │                                           │
┌─Key─┐│         ┌─────────┐         ┌─────────┐│
│Hash ├┘         │ Virtual │         │ Virtual │└
└─────┘          │ Node 1.2│         │ Node 2.2│
                 └─────────┘         └─────────┘
```
"""

import hashlib
import bisect
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import random

@dataclass
class VirtualNode:
    """Represents a virtual node in the hash ring"""
    physical_node: str
    index: int
    hash_value: int

class ConsistentHash:
    """Implements consistent hashing with virtual nodes"""
    
    def __init__(self, nodes: List[str], virtual_nodes: int = 3):
        self.virtual_nodes = virtual_nodes
        self.hash_ring: List[VirtualNode] = []
        self.nodes: Dict[str, List[VirtualNode]] = {}
        
        # Add initial nodes
        for node in nodes:
            self.add_node(node)
    
    def _hash(self, key: str) -> int:
        """Generate hash for a key"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_node(self, node: str):
        """Add a new node to the hash ring"""
        if node in self.nodes:
            return
        
        # Create virtual nodes
        virtual_nodes = []
        for i in range(self.virtual_nodes):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            vnode = VirtualNode(node, i, hash_value)
            virtual_nodes.append(vnode)
            bisect.insort(self.hash_ring, vnode, key=lambda x: x.hash_value)
        
        self.nodes[node] = virtual_nodes
    
    def remove_node(self, node: str):
        """Remove a node and its virtual nodes from the hash ring"""
        if node not in self.nodes:
            return
        
        # Remove virtual nodes
        virtual_nodes = self.nodes[node]
        for vnode in virtual_nodes:
            idx = bisect.bisect_left(self.hash_ring, vnode, key=lambda x: x.hash_value)
            if idx < len(self.hash_ring) and self.hash_ring[idx].hash_value == vnode.hash_value:
                self.hash_ring.pop(idx)
        
        del self.nodes[node]
    
    def get_node(self, key: str) -> Optional[str]:
        """Get the node responsible for a key"""
        if not self.hash_ring:
            return None
        
        hash_value = self._hash(key)
        idx = bisect.bisect(self.hash_ring, VirtualNode("", 0, hash_value), key=lambda x: x.hash_value)
        
        # Wrap around to the first node if we're at the end
        if idx >= len(self.hash_ring):
            idx = 0
        
        return self.hash_ring[idx].physical_node

class ShardedDatabase:
    """Example of a sharded database using consistent hashing"""
    
    def __init__(self, shard_nodes: List[str]):
        self.hasher = ConsistentHash(shard_nodes)
        self.shards: Dict[str, Dict[str, Any]] = {
            node: {} for node in shard_nodes
        }
    
    def set(self, key: str, value: Any):
        """Store a value in the appropriate shard"""
        shard = self.hasher.get_node(key)
        if shard:
            self.shards[shard][key] = value
            return True
        return False
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the appropriate shard"""
        shard = self.hasher.get_node(key)
        if shard:
            return self.shards[shard].get(key)
        return None
    
    def add_shard(self, node: str):
        """Add a new shard to the database"""
        self.hasher.add_node(node)
        self.shards[node] = {}
        
        # Rebalance data
        self._rebalance()
    
    def remove_shard(self, node: str):
        """Remove a shard from the database"""
        if node not in self.shards:
            return
        
        # Save data before removing the shard
        data_to_migrate = self.shards[node]
        
        # Remove the shard
        self.hasher.remove_node(node)
        del self.shards[node]
        
        # Rebalance the data
        for key, value in data_to_migrate.items():
            self.set(key, value)
    
    def _rebalance(self):
        """Rebalance data across shards"""
        all_data = []
        for shard_data in self.shards.values():
            all_data.extend(shard_data.items())
        
        # Clear all shards
        for shard in self.shards.values():
            shard.clear()
        
        # Redistribute data
        for key, value in all_data:
            self.set(key, value)
    
    def get_shard_stats(self) -> Dict[str, int]:
        """Get statistics about data distribution across shards"""
        return {node: len(data) for node, data in self.shards.items()}

def demonstrate_sharding():
    """Demonstrate sharding functionality"""
    # Initialize sharded database
    initial_shards = ["shard1", "shard2", "shard3"]
    db = ShardedDatabase(initial_shards)
    
    # Insert some test data
    test_data = {
        f"user_{i}": f"data_{i}" for i in range(100)
    }
    
    print("Initial data distribution:")
    print("-" * 50)
    
    for key, value in test_data.items():
        db.set(key, value)
    
    print("Data distribution across shards:")
    for shard, count in db.get_shard_stats().items():
        print(f"{shard}: {count} records")
    
    # Add a new shard
    print("\nAdding new shard 'shard4'...")
    db.add_shard("shard4")
    
    print("\nData distribution after adding shard:")
    for shard, count in db.get_shard_stats().items():
        print(f"{shard}: {count} records")
    
    # Remove a shard
    print("\nRemoving 'shard2'...")
    db.remove_shard("shard2")
    
    print("\nData distribution after removing shard:")
    for shard, count in db.get_shard_stats().items():
        print(f"{shard}: {count} records")
    
    # Demonstrate data access
    print("\nAccessing data:")
    test_keys = random.sample(list(test_data.keys()), 5)
    for key in test_keys:
        value = db.get(key)
        shard = db.hasher.get_node(key)
        print(f"Key: {key}, Value: {value}, Shard: {shard}")

if __name__ == "__main__":
    demonstrate_sharding() 