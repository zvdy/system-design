"""
Load Balancer Implementation

This module demonstrates different load balancing algorithms and health checking mechanisms.
It includes implementations of Round Robin, Least Connections, and Weighted Round Robin.

ASCII Diagram:
```
┌──────────┐
│ Client   │◄──┐
└──────────┘   │
               │
┌──────────────▼─────────────┐
│        Load Balancer       │
├────────────┬───────────────┤
│ Algorithm  │ Health Check  │
└────────────┴──┬────────────┘
                │
        ┌───────┼───────┐
        │       │       │
    ┌───▼─┐ ┌───▼─┐ ┌───▼─┐
    │Srv 1│ │Srv 2│ │Srv 3│
    └─────┘ └─────┘ └─────┘
```
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import random
import threading
from collections import defaultdict
import heapq
from abc import ABC, abstractmethod

class HealthStatus(Enum):
    """Server health status"""
    HEALTHY = "Healthy"
    UNHEALTHY = "Unhealthy"
    UNKNOWN = "Unknown"

@dataclass
class Server:
    """Represents a backend server"""
    id: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 100
    current_connections: int = 0
    health_status: HealthStatus = HealthStatus.UNKNOWN
    last_health_check: float = 0.0

    def __hash__(self):
        return hash(self.id)

class LoadBalancingAlgorithm(ABC):
    """Abstract base class for load balancing algorithms"""
    
    @abstractmethod
    def select_server(self, servers: List[Server]) -> Optional[Server]:
        """Select a server based on the algorithm"""
        pass

class RoundRobin(LoadBalancingAlgorithm):
    """Round Robin load balancing"""
    
    def __init__(self):
        self.current_index = 0
        self._lock = threading.Lock()
    
    def select_server(self, servers: List[Server]) -> Optional[Server]:
        if not servers:
            return None
        
        with self._lock:
            # Skip unhealthy servers
            healthy_servers = [s for s in servers if s.health_status == HealthStatus.HEALTHY]
            if not healthy_servers:
                return None
            
            selected = healthy_servers[self.current_index % len(healthy_servers)]
            self.current_index += 1
            return selected

class WeightedRoundRobin(LoadBalancingAlgorithm):
    """Weighted Round Robin load balancing"""
    
    def __init__(self):
        self.current_weights: Dict[str, int] = {}
        self._lock = threading.Lock()
    
    def select_server(self, servers: List[Server]) -> Optional[Server]:
        if not servers:
            return None
        
        with self._lock:
            healthy_servers = [s for s in servers if s.health_status == HealthStatus.HEALTHY]
            if not healthy_servers:
                return None
            
            # Initialize current weights if needed
            for server in healthy_servers:
                if server.id not in self.current_weights:
                    self.current_weights[server.id] = server.weight
            
            # Find server with highest current weight
            max_weight = -1
            selected = None
            
            for server in healthy_servers:
                if server.id in self.current_weights:
                    weight = self.current_weights[server.id]
                    if weight > max_weight:
                        max_weight = weight
                        selected = server
            
            if selected:
                # Adjust weights
                for server in healthy_servers:
                    if server.id in self.current_weights:
                        self.current_weights[server.id] += server.weight
                self.current_weights[selected.id] -= sum(s.weight for s in healthy_servers)
            
            return selected

class LeastConnections(LoadBalancingAlgorithm):
    """Least Connections load balancing"""
    
    def select_server(self, servers: List[Server]) -> Optional[Server]:
        if not servers:
            return None
        
        healthy_servers = [s for s in servers if s.health_status == HealthStatus.HEALTHY]
        if not healthy_servers:
            return None
        
        # Select server with least current connections
        return min(healthy_servers, key=lambda s: s.current_connections)

class HealthChecker:
    """Health checker for backend servers"""
    
    def __init__(self, check_interval: float = 5.0):
        self.check_interval = check_interval
        self.running = False
        self._lock = threading.Lock()
    
    def check_health(self, server: Server) -> HealthStatus:
        """Simulate health check (in real implementation, would make HTTP/TCP request)"""
        try:
            # Simulate network call
            time.sleep(0.1)
            # 90% chance of being healthy
            is_healthy = random.random() < 0.9
            return HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
        except Exception:
            return HealthStatus.UNHEALTHY
    
    def start_health_checks(self, servers: List[Server]):
        """Start periodic health checks"""
        self.running = True
        
        def check_loop():
            while self.running:
                for server in servers:
                    with self._lock:
                        status = self.check_health(server)
                        server.health_status = status
                        server.last_health_check = time.time()
                time.sleep(self.check_interval)
        
        thread = threading.Thread(target=check_loop)
        thread.daemon = True
        thread.start()
    
    def stop_health_checks(self):
        """Stop health checks"""
        self.running = False

class LoadBalancer:
    """Load balancer implementation"""
    
    def __init__(self, algorithm: LoadBalancingAlgorithm):
        self.algorithm = algorithm
        self.servers: List[Server] = []
        self.health_checker = HealthChecker()
        self._lock = threading.Lock()
    
    def add_server(self, server: Server):
        """Add a backend server"""
        with self._lock:
            self.servers.append(server)
    
    def remove_server(self, server_id: str):
        """Remove a backend server"""
        with self._lock:
            self.servers = [s for s in servers if s.id != server_id]
    
    def get_server(self) -> Optional[Server]:
        """Get next server based on load balancing algorithm"""
        return self.algorithm.select_server(self.servers)
    
    def start(self):
        """Start the load balancer"""
        self.health_checker.start_health_checks(self.servers)
    
    def stop(self):
        """Stop the load balancer"""
        self.health_checker.stop_health_checks()

def simulate_request(server: Server):
    """Simulate a request to a server"""
    server.current_connections += 1
    try:
        # Simulate processing time
        time.sleep(random.uniform(0.1, 0.3))
    finally:
        server.current_connections -= 1

def demonstrate_load_balancing():
    """Demonstrate different load balancing algorithms"""
    
    # Create servers
    servers = [
        Server("s1", "server1.example.com", 8001, weight=1),
        Server("s2", "server2.example.com", 8002, weight=2),
        Server("s3", "server3.example.com", 8003, weight=1)
    ]
    
    # Round Robin Example
    print("Round Robin Example:")
    print("-" * 50)
    
    lb_rr = LoadBalancer(RoundRobin())
    for server in servers:
        lb_rr.add_server(server)
    
    lb_rr.start()
    time.sleep(1)  # Wait for initial health checks
    
    print("\nServer selection sequence:")
    for _ in range(6):
        server = lb_rr.get_server()
        if server:
            print(f"Selected: {server.id} (Status: {server.health_status.value})")
    
    # Weighted Round Robin Example
    print("\nWeighted Round Robin Example:")
    print("-" * 50)
    
    lb_wrr = LoadBalancer(WeightedRoundRobin())
    for server in servers:
        lb_wrr.add_server(server)
    
    lb_wrr.start()
    time.sleep(1)
    
    print("\nServer selection sequence:")
    for _ in range(6):
        server = lb_wrr.get_server()
        if server:
            print(f"Selected: {server.id} (Weight: {server.weight})")
    
    # Least Connections Example
    print("\nLeast Connections Example:")
    print("-" * 50)
    
    lb_lc = LoadBalancer(LeastConnections())
    for server in servers:
        lb_lc.add_server(server)
    
    lb_lc.start()
    time.sleep(1)
    
    # Simulate some existing connections
    servers[0].current_connections = 5
    servers[1].current_connections = 2
    servers[2].current_connections = 8
    
    print("\nServer selection with connection counts:")
    for _ in range(3):
        server = lb_lc.get_server()
        if server:
            print(f"Selected: {server.id} (Connections: {server.current_connections})")
    
    # Clean up
    lb_rr.stop()
    lb_wrr.stop()
    lb_lc.stop()

if __name__ == "__main__":
    print("Running Load Balancing Example")
    demonstrate_load_balancing() 