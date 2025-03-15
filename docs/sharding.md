# Database Sharding 

This section covers database sharding strategies and their implementation in distributed systems.

## Overview

Sharding is a database architecture pattern where data is horizontally partitioned across multiple database instances to improve scalability and performance.

## Sharding Strategies

### 1. Range-Based Sharding
```
┌─────────────┐
│ User ID     │
├─────────────┤
│ 1-1000      │──► Shard 1
│ 1001-2000   │──► Shard 2
│ 2001-3000   │──► Shard 3
└─────────────┘
```

- Simple to implement
- Good for sequential access
- Potential for hot spots
- Uneven distribution

### 2. Hash-Based Sharding
```
┌─────────────┐
│ Key Hash    │
├─────────────┤
│ hash % 3 = 0│──► Shard 1
│ hash % 3 = 1│──► Shard 2
│ hash % 3 = 2│──► Shard 3
└─────────────┘
```

- Even distribution
- No hot spots
- Difficult to resize
- No range queries

### 3. Consistent Hashing
```
        Shard 1
           │
    359° ───┼──── 0°
            │
     270° ──┼── 90°
            │
        180°
        Shard 2
```

- Minimal redistribution
- Dynamic scaling
- Complex implementation
- Good distribution

### 4. Directory-Based Sharding
```
┌─────────────┐     ┌─────────────┐
│   Lookup    │     │   Shards    │
│   Service   │────►│   1,2,3     │
└─────────────┘     └─────────────┘
```

- Flexible mapping
- Additional complexity
- Single point of failure
- Easy to change

## Shard Operations

### 1. Shard Split
```
┌─────────┐      ┌─────────┐
│ Shard A │─────►│Shard A1 │
└─────────┘      └─────────┘
                 ┌─────────┐
                 │Shard A2 │
                 └─────────┘
```

### 2. Shard Merge
```
┌─────────┐
│Shard B1 │──┐
└─────────┘  │   ┌─────────┐
             ├──►│ Shard B │
┌─────────┐  │   └─────────┘
│Shard B2 │──┘
└─────────┘
```

### 3. Rebalancing
```
Before:
Shard 1 (40%) ─── Shard 2 (30%) ─── Shard 3 (30%)

After:
Shard 1 (33%) ─── Shard 2 (33%) ─── Shard 3 (34%)
```

## Implementation Considerations

### 1. Shard Key Selection
```
┌─────────────┐
│ Shard Keys  │
├─────────────┤
│ User ID     │
│ Location    │
│ Timestamp   │
│ Custom Hash │
└─────────────┘
```

Criteria:
- Even distribution
- Query patterns
- Growth patterns
- Cardinality

### 2. Cross-Shard Operations
```
┌─────────┐   ┌─────────┐   ┌─────────┐
│ Shard 1 │   │ Shard 2 │   │ Shard 3 │
└────┬────┘   └────┬────┘   └────┬────┘
     │             │             │
     └─────────────┼─────────────┘
                   │
            Distributed Query
```

Challenges:
- Transactions
- Joins
- Consistency
- Performance

### 3. Monitoring and Maintenance
```
┌─────────────┐
│ Metrics     │
├─────────────┤
│ Size        │
│ Load        │
│ Latency     │
│ Error Rate  │
└─────────────┘
```

## Best Practices

1. **Design Phase**
   - Choose appropriate shard key
   - Plan for growth
   - Consider query patterns
   - Design for failure

2. **Implementation**
   - Use consistent hashing
   - Implement proper monitoring
   - Handle cross-shard operations
   - Maintain redundancy

3. **Operations**
   - Monitor shard balance
   - Plan maintenance windows
   - Regular backups
   - Test failover

## Common Pitfalls

1. **Hot Spots**
```
┌─────────┐
│ Shard 1 │ ◄─── 80% of traffic
└─────────┘
┌─────────┐
│ Shard 2 │ ◄─── 10% of traffic
└─────────┘
┌─────────┐
│ Shard 3 │ ◄─── 10% of traffic
└─────────┘
```

2. **Cross-Shard Joins**
```
Query ──┬──► Shard 1 ──┐
        ├──► Shard 2 ──┼──► Merge Results
        └──► Shard 3 ──┘
```

3. **Rebalancing Issues**
```
Migration in Progress
┌─────────┐   ╳   ┌─────────┐
│ Shard A │───╳───│ Shard B │
└─────────┘   ╳   └─────────┘
    Network Partition
```

## Implementation Example

See the [Consistent Hashing Implementation](../src/examples/sharding/consistent_hashing.py) for a practical demonstration of sharding strategies. 