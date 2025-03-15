# Database Replication 

This section covers database replication patterns and their implementation in distributed systems.

## Overview

Database replication is the process of maintaining multiple copies of data across different locations to improve availability, fault tolerance, and read performance.

## Replication Patterns

### 1. Master-Slave Replication
```
                  ┌──────────┐
            ┌────►│ Replica 1│ (Read-Only)
            │     └──────────┘
┌──────────┐│     ┌──────────┐
│  Master  ├┼────►│ Replica 2│ (Read-Only)
└──────────┘│     └──────────┘
   (Write)  │     ┌──────────┐
            └────►│ Replica 3│ (Read-Only)
                  └──────────┘
```

- Single master handles all writes
- Multiple read-only replicas
- Asynchronous replication
- Good for read-heavy workloads

### 2. Multi-Master Replication
```
┌──────────┐     ┌──────────┐
│ Master 1 │◄───►│ Master 2 │
└──────────┘     └──────────┘
      ▲               ▲
      │               │
      ▼               ▼
┌──────────┐     ┌──────────┐
│ Master 3 │◄───►│ Master 4 │
└──────────┘     └──────────┘
```

- Multiple masters accept writes
- Complex conflict resolution
- Higher availability
- Eventual consistency

### 3. Circular Replication
```
┌──────────┐
│ Node 1   │
└────┬─────┘
     │
     ▼
┌──────────┐
│ Node 2   │
└────┬─────┘
     │
     ▼
┌──────────┐
│ Node 3   │
└────┬─────┘
     │
     └────►
```

- Each node replicates to next node
- Simple to implement
- Single point of failure
- Limited scalability

## Replication Methods

### 1. Synchronous Replication
```
┌────────┐    ┌────────┐    ┌────────┐
│ Client │───►│ Master │───►│Replica │
└────────┘    └────────┘    └────────┘
     ▲            │             │
     └────────────┴─────────────┘
        Wait for confirmation
```

- Stronger consistency
- Higher latency
- Better durability
- Risk of unavailability

### 2. Asynchronous Replication
```
┌────────┐    ┌────────┐    ┌────────┐
│ Client │───►│ Master │    │Replica │
└────────┘    └────────┘    └────────┘
     ▲            │      ╱
     └────────────┘    ╱
     Quick response  Async
                   ╱
```

- Lower latency
- Better performance
- Eventual consistency
- Possible data loss

## Conflict Resolution

### 1. Timestamp-Based
```
Record 1 (t=1) ──► Record 2 (t=2) ──► Record 3 (t=3)
                                          ▲
                                    Latest wins
```

### 2. Vector Clocks
```
┌─────────┐
│ A:1 B:2 │ Node A's version vector
└─────────┘
     ║
┌─────────┐
│ A:2 B:2 │ After local update
└─────────┘
```

### 3. Custom Resolution
```
┌──────────┐
│ Version 1│
└────┬─────┘
     │
┌────┴─────┐
│ Conflict │
└────┬─────┘
     │
┌────┴─────┐
│ Resolved │
└──────────┘
```

## Implementation Considerations

### 1. Consistency Levels
```
┌───────────┐
│ Strong    │ All replicas in sync
├───────────┤
│ Eventual  │ Replicas will sync eventually
├───────────┤
│ Causal    │ Related changes are ordered
└───────────┘
```

### 2. Failure Detection
```
┌──────────┐    ╳    ┌──────────┐
│ Master   │────╳────│ Replica  │
└──────────┘    ╳    └──────────┘
                ╳
         Network Partition
```

- Heartbeat mechanisms
- Timeout settings
- Split-brain prevention

### 3. Recovery Process
```
1. Detect failure
   ┌──────────┐
   │ Failed   │
   └──────────┘

2. Initialize recovery
   ┌──────────┐
   │Recovery  │
   └──────────┘

3. Catch up
   ┌──────────┐
   │ Syncing  │
   └──────────┘

4. Resume normal operation
   ┌──────────┐
   │ Active   │
   └──────────┘
```

## Best Practices

1. **Design**
   - Plan for network partitions
   - Choose appropriate consistency levels
   - Consider geographic distribution

2. **Implementation**
   - Use WAL (Write-Ahead Logging)
   - Implement proper monitoring
   - Handle edge cases

3. **Maintenance**
   - Regular health checks
   - Backup strategies
   - Failover testing

## Implementation Example

See the [Master-Slave Replication](../src/examples/replication/master_slave_replication.py) for a practical demonstration of replication patterns. 