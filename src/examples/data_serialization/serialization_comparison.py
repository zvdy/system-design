"""
Data Serialization Comparison

This module demonstrates different serialization formats:
1. Protocol Buffers (protobuf)
2. JSON
3. MessagePack
4. Apache Avro

ASCII Diagram:
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Python    │     │ Serialized   │     │  Python     │
│   Object    │────►│    Data      │────►│  Object     │
└─────────────┘     └──────────────┘     └─────────────┘
     ▲                     │                    ▲
     │                     ▼                    │
     │              ┌──────────────┐           │
     │              │  Transport   │           │
     └──────────────┤   Layer     ├───────────┘
                    └──────────────┘
```
"""

import json
import time
import msgpack
import fastavro
from dataclasses import dataclass
from typing import List, Dict
from google.protobuf import json_format
from concurrent.futures import ThreadPoolExecutor
import user_pb2  # Generated from user.proto
import io

@dataclass
class UserProfile:
    """Sample user profile for serialization comparison"""
    user_id: int
    username: str
    email: str
    age: int
    interests: List[str]
    metadata: Dict[str, str]

def create_sample_data() -> UserProfile:
    """Create a sample user profile"""
    return UserProfile(
        user_id=12345,
        username="john_doe",
        email="john@example.com",
        age=30,
        interests=["programming", "system design", "databases"],
        metadata={
            "last_login": "2024-01-20T10:00:00Z",
            "account_type": "premium",
            "region": "us-west"
        }
    )

def benchmark_json(data: UserProfile, iterations: int = 1000):
    """Benchmark JSON serialization"""
    start_time = time.time()
    
    for _ in range(iterations):
        # Serialize
        json_data = json.dumps(data.__dict__)
        # Deserialize
        json.loads(json_data)
    
    end_time = time.time()
    return end_time - start_time

def benchmark_msgpack(data: UserProfile, iterations: int = 1000):
    """Benchmark MessagePack serialization"""
    start_time = time.time()
    
    for _ in range(iterations):
        # Serialize
        msgpack_data = msgpack.packb(data.__dict__)
        # Deserialize
        msgpack.unpackb(msgpack_data)
    
    end_time = time.time()
    return end_time - start_time

def benchmark_protobuf(data: UserProfile, iterations: int = 1000):
    """Benchmark Protocol Buffers serialization"""
    # Convert to protobuf message
    proto_user = user_pb2.User()
    proto_user.user_id = data.user_id
    proto_user.username = data.username
    proto_user.email = data.email
    proto_user.age = data.age
    proto_user.interests.extend(data.interests)
    for key, value in data.metadata.items():
        proto_user.metadata[key] = value
    
    start_time = time.time()
    
    for _ in range(iterations):
        # Serialize
        proto_data = proto_user.SerializeToString()
        # Deserialize
        new_user = user_pb2.User()
        new_user.ParseFromString(proto_data)
    
    end_time = time.time()
    return end_time - start_time

def benchmark_avro(data: UserProfile, iterations: int = 1000):
    """Benchmark Apache Avro serialization"""
    schema = {
        "type": "record",
        "name": "User",
        "fields": [
            {"name": "user_id", "type": "int"},
            {"name": "username", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "age", "type": "int"},
            {"name": "interests", "type": {"type": "array", "items": "string"}},
            {"name": "metadata", "type": {"type": "map", "values": "string"}}
        ]
    }
    
    start_time = time.time()
    
    for _ in range(iterations):
        # Serialize
        avro_data = fastavro.writer(bytes_io := io.BytesIO(), schema, [data.__dict__])
        bytes_io.seek(0)
        # Deserialize
        list(fastavro.reader(bytes_io))
    
    end_time = time.time()
    return end_time - start_time

def parallel_benchmark(data: UserProfile, iterations: int = 1000):
    """Run benchmarks in parallel"""
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(benchmark_json, data, iterations),
            executor.submit(benchmark_msgpack, data, iterations),
            executor.submit(benchmark_protobuf, data, iterations),
            executor.submit(benchmark_avro, data, iterations)
        ]
        
        results = [future.result() for future in futures]
        
    return {
        "JSON": results[0],
        "MessagePack": results[1],
        "Protocol Buffers": results[2],
        "Apache Avro": results[3]
    }

def format_size(data: UserProfile):
    """Compare serialized data sizes"""
    # JSON
    json_size = len(json.dumps(data.__dict__).encode())
    
    # MessagePack
    msgpack_size = len(msgpack.packb(data.__dict__))
    
    # Protocol Buffers
    proto_user = user_pb2.User()
    proto_user.user_id = data.user_id
    proto_user.username = data.username
    proto_user.email = data.email
    proto_user.age = data.age
    proto_user.interests.extend(data.interests)
    for key, value in data.metadata.items():
        proto_user.metadata[key] = value
    protobuf_size = len(proto_user.SerializeToString())
    
    # Apache Avro
    schema = {
        "type": "record",
        "name": "User",
        "fields": [
            {"name": "user_id", "type": "int"},
            {"name": "username", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "age", "type": "int"},
            {"name": "interests", "type": {"type": "array", "items": "string"}},
            {"name": "metadata", "type": {"type": "map", "values": "string"}}
        ]
    }
    bytes_io = io.BytesIO()
    fastavro.writer(bytes_io, schema, [data.__dict__])
    avro_size = len(bytes_io.getvalue())
    
    return {
        "JSON": json_size,
        "MessagePack": msgpack_size,
        "Protocol Buffers": protobuf_size,
        "Apache Avro": avro_size
    }

if __name__ == "__main__":
    # Create sample data
    user_data = create_sample_data()
    
    print("Running serialization benchmarks...")
    results = parallel_benchmark(user_data)
    
    print("\nPerformance Results (1000 iterations):")
    print("-" * 50)
    for format_name, duration in results.items():
        print(f"{format_name:15} : {duration:.4f} seconds")
    
    print("\nSerialized Data Sizes:")
    print("-" * 50)
    sizes = format_size(user_data)
    for format_name, size in sizes.items():
        print(f"{format_name:15} : {size} bytes") 