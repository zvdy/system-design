"""
Stream Processing Implementation

This module demonstrates real-time stream processing with windowing and analytics.
It includes examples of different window types and stream operations.

ASCII Diagram:
```
Data Stream
    │
    ▼
┌─────────────────┐
│ Stream Source   │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│    Windows      │
│ ┌───┐ ┌───┐    │
│ │ T │ │ T │    │
│ └───┘ └───┘    │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│   Processing    │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│     Sink        │
└─────────────────┘
```
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from collections import deque
import time
from datetime import datetime, timedelta
import json
import threading
import queue
import random

@dataclass
class Event:
    """Represents a streaming event"""
    timestamp: datetime
    value: Any
    key: Optional[str] = None

class Window:
    """Base class for windowing strategies"""
    def __init__(self, size: timedelta):
        self.size = size
        self.events: List[Event] = []
    
    def add_event(self, event: Event) -> bool:
        """Add event to window, return True if window is ready for processing"""
        raise NotImplementedError
    
    def get_events(self) -> List[Event]:
        """Get events in the window"""
        return self.events.copy()
    
    def clear(self):
        """Clear the window"""
        self.events = []

class TumblingWindow(Window):
    """Fixed-size, non-overlapping windows"""
    def __init__(self, size: timedelta):
        super().__init__(size)
        self.window_start: Optional[datetime] = None
    
    def add_event(self, event: Event) -> bool:
        if not self.window_start:
            self.window_start = event.timestamp
        
        if event.timestamp - self.window_start < self.size:
            self.events.append(event)
            return False
        
        return True

class SlidingWindow(Window):
    """Overlapping windows that slide by a fixed duration"""
    def __init__(self, size: timedelta, slide: timedelta):
        super().__init__(size)
        self.slide = slide
        self.window_start: Optional[datetime] = None
    
    def add_event(self, event: Event) -> bool:
        if not self.window_start:
            self.window_start = event.timestamp
        
        self.events.append(event)
        
        # Remove events outside the window
        while self.events and event.timestamp - self.events[0].timestamp >= self.size:
            self.events.pop(0)
        
        return event.timestamp - self.window_start >= self.slide

class StreamProcessor:
    """Stream processing engine with windowing support"""
    
    def __init__(self):
        self.sources: List[queue.Queue] = []
        self.windows: Dict[str, Window] = {}
        self.processors: Dict[str, Callable] = {}
        self.sinks: List[Callable] = []
        self.running = False
    
    def add_source(self, source: queue.Queue):
        """Add a data source"""
        self.sources.append(source)
    
    def add_window(self, name: str, window: Window):
        """Add a window configuration"""
        self.windows[name] = window
    
    def add_processor(self, name: str, func: Callable):
        """Add a processing function"""
        self.processors[name] = func
    
    def add_sink(self, sink: Callable):
        """Add an output sink"""
        self.sinks.append(sink)
    
    def process_windows(self):
        """Process events in windows"""
        for window_name, window in self.windows.items():
            if window.events:
                # Process window if ready
                for processor_name, processor in self.processors.items():
                    result = processor(window.get_events())
                    # Send to sinks
                    for sink in self.sinks:
                        sink(window_name, processor_name, result)
                
                window.clear()
    
    def run(self):
        """Start processing the stream"""
        self.running = True
        
        while self.running:
            # Process all sources
            for source in self.sources:
                try:
                    event = source.get_nowait()
                    # Add to all windows
                    for window in self.windows.values():
                        if window.add_event(event):
                            self.process_windows()
                except queue.Empty:
                    continue
            
            time.sleep(0.1)  # Prevent busy waiting
    
    def stop(self):
        """Stop processing"""
        self.running = False

# Example processors
def count_processor(events: List[Event]) -> int:
    """Count events in window"""
    return len(events)

def average_processor(events: List[Event]) -> float:
    """Calculate average of numeric events"""
    if not events:
        return 0.0
    return sum(event.value for event in events) / len(events)

def demonstrate_stream_processing():
    """Demonstrate stream processing functionality"""
    # Create stream processor
    processor = StreamProcessor()
    
    # Add data source
    source = queue.Queue()
    processor.add_source(source)
    
    # Add windows
    processor.add_window("tumbling", TumblingWindow(timedelta(seconds=5)))
    processor.add_window("sliding", SlidingWindow(timedelta(seconds=10), timedelta(seconds=5)))
    
    # Add processors
    processor.add_processor("count", count_processor)
    processor.add_processor("average", average_processor)
    
    # Add sink
    def print_sink(window_name: str, processor_name: str, result: Any):
        print(f"Window: {window_name}, Processor: {processor_name}, Result: {result}")
    
    processor.add_sink(print_sink)
    
    # Start processing in a separate thread
    process_thread = threading.Thread(target=processor.run)
    process_thread.start()
    
    # Generate sample data
    print("Generating sample data...")
    start_time = datetime.now()
    
    for i in range(20):
        event = Event(
            timestamp=start_time + timedelta(seconds=i),
            value=random.randint(1, 100)
        )
        source.put(event)
        time.sleep(1)  # Simulate real-time data
    
    # Stop processing
    processor.stop()
    process_thread.join()

if __name__ == "__main__":
    print("Running Stream Processing Example")
    demonstrate_stream_processing() 