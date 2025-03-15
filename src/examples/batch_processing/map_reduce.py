"""
MapReduce Implementation Example

This module demonstrates a simple MapReduce framework for batch processing.
It includes a word count example and a log analysis example.

ASCII Diagram:
```
Input Data
    │
    ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Map 1   │    │ Map 2   │    │ Map 3   │
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     ▼              ▼              ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Shuffle │    │ Shuffle │    │ Shuffle │
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     ▼              ▼              ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│Reduce 1 │    │Reduce 2 │    │Reduce 3 │
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     └──────────────┼──────────────┘
                    ▼
               Final Result
```
"""

from typing import List, Dict, Any, Callable, Iterator
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import itertools
import re
from collections import Counter
from datetime import datetime
import json

@dataclass
class MapReduceJob:
    """Represents a MapReduce job configuration"""
    name: str
    input_data: List[Any]
    map_func: Callable
    reduce_func: Callable
    num_workers: int = multiprocessing.cpu_count()

class MapReduce:
    """Simple MapReduce implementation"""
    
    def __init__(self, job: MapReduceJob):
        self.job = job
    
    def _partition(self, mapped_data: Iterator[tuple]) -> Dict[Any, List[Any]]:
        """Partition data by key for reducers"""
        partitioned = {}
        for key, value in mapped_data:
            if key not in partitioned:
                partitioned[key] = []
            partitioned[key].append(value)
        return partitioned
    
    def run(self) -> Dict[Any, Any]:
        """Execute the MapReduce job"""
        print(f"Starting MapReduce job: {self.job.name}")
        
        # Map phase
        print("Map phase...")
        with ProcessPoolExecutor(max_workers=self.job.num_workers) as executor:
            mapped_data = executor.map(self.job.map_func, self.job.input_data)
        
        # Flatten mapped data
        mapped_data = list(itertools.chain.from_iterable(mapped_data))
        
        # Shuffle phase
        print("Shuffle phase...")
        partitioned_data = self._partition(mapped_data)
        
        # Reduce phase
        print("Reduce phase...")
        with ProcessPoolExecutor(max_workers=self.job.num_workers) as executor:
            reduced_data = {}
            for key, values in partitioned_data.items():
                reduced_data[key] = executor.submit(self.job.reduce_func, key, values)
            
            # Get results
            return {key: future.result() for key, future in reduced_data.items()}

# Example 1: Word Count
def word_count_map(text: str) -> List[tuple]:
    """Map function for word count"""
    words = re.findall(r'\w+', text.lower())
    return [(word, 1) for word in words]

def word_count_reduce(key: str, values: List[int]) -> int:
    """Reduce function for word count"""
    return sum(values)

# Example 2: Log Analysis
@dataclass
class LogEntry:
    """Represents a log entry"""
    timestamp: datetime
    level: str
    message: str

def parse_log_line(line: str) -> LogEntry:
    """Parse a log line into a LogEntry"""
    # Example format: "2024-01-20 10:00:00 INFO User logged in"
    timestamp_str, level, *message_parts = line.split()
    return LogEntry(
        timestamp=datetime.fromisoformat(timestamp_str.replace('T', ' ')),
        level=level,
        message=' '.join(message_parts)
    )

def log_analysis_map(log_line: str) -> List[tuple]:
    """Map function for log analysis"""
    try:
        entry = parse_log_line(log_line)
        return [(entry.level, 1), 
                (f"hour_{entry.timestamp.hour}", 1)]
    except Exception:
        return []

def log_analysis_reduce(key: str, values: List[int]) -> int:
    """Reduce function for log analysis"""
    return sum(values)

def demonstrate_word_count():
    """Demonstrate word count MapReduce"""
    # Sample text data
    texts = [
        "Hello world hello python",
        "MapReduce is a programming model",
        "Python is awesome awesome",
        "Hello MapReduce world"
    ]
    
    # Create and run job
    job = MapReduceJob(
        name="Word Count",
        input_data=texts,
        map_func=word_count_map,
        reduce_func=word_count_reduce
    )
    
    mapreduce = MapReduce(job)
    result = mapreduce.run()
    
    print("\nWord Count Results:")
    print("-" * 50)
    for word, count in sorted(result.items()):
        print(f"{word}: {count}")

def demonstrate_log_analysis():
    """Demonstrate log analysis MapReduce"""
    # Sample log data
    logs = [
        "2024-01-20T10:00:00 INFO User logged in",
        "2024-01-20T10:05:00 ERROR Database connection failed",
        "2024-01-20T10:10:00 INFO User action completed",
        "2024-01-20T11:00:00 WARNING System running low on memory",
        "2024-01-20T11:05:00 INFO User logged out",
        "2024-01-20T11:10:00 ERROR Service unavailable"
    ]
    
    # Create and run job
    job = MapReduceJob(
        name="Log Analysis",
        input_data=logs,
        map_func=log_analysis_map,
        reduce_func=log_analysis_reduce
    )
    
    mapreduce = MapReduce(job)
    result = mapreduce.run()
    
    print("\nLog Analysis Results:")
    print("-" * 50)
    print("\nLog Levels:")
    for key, count in sorted(result.items()):
        if not key.startswith('hour_'):
            print(f"{key}: {count}")
    
    print("\nHourly Distribution:")
    for key, count in sorted(result.items()):
        if key.startswith('hour_'):
            hour = key.split('_')[1]
            print(f"Hour {hour}: {count}")

if __name__ == "__main__":
    print("Running MapReduce Examples\n")
    
    print("1. Word Count Example")
    demonstrate_word_count()
    
    print("\n2. Log Analysis Example")
    demonstrate_log_analysis() 