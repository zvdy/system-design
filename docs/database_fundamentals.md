# Database Fundamentals 

This section covers the core concepts of database systems and their implementation in modern applications.

## ACID Properties

ACID is an acronym that stands for:

### Atomicity
```
┌─────────────────┐
│   Transaction   │
│    succeeds    ─┼─── All changes applied
│      or         │
│     fails      ─┼─── No changes applied
└─────────────────┘
```

- All operations in a transaction must succeed, or none are applied
- If any operation fails, the entire transaction is rolled back
- Example: Bank transfer must either complete fully or not at all

### Consistency
```
┌─────────────────┐      ┌─────────────┐      ┌─────────────────┐
│   Valid State   │─────►│Transaction  │─────►│   Valid State   │
└─────────────────┘      └─────────────┘      └─────────────────┘
```

- Database must remain in a valid state before and after transactions
- All constraints, cascades, and triggers must be satisfied
- Example: Account balance cannot go negative

### Isolation
```
Transaction 1    ├────────┼────────┤
Transaction 2         ├────────┼────────┤
                Time ─────────────────────►
```

- Concurrent transactions must not interfere with each other
- Different isolation levels provide different guarantees
- Example: Two users withdrawing money simultaneously

### Durability
```
┌─────────────┐    ┌─────────────┐
│Transaction  │───►│  Committed  │────┐
└─────────────┘    └─────────────┘    │
                                      ▼
                               ┌─────────────┐
                               │  Persisted  │
                               │    Data     │
                               └─────────────┘
```

- Once committed, transactions must persist even after system failures
- Usually implemented through write-ahead logging (WAL)
- Example: Saved data survives power outages

## Implementation Example

See the [ACID Properties Implementation](../src/examples/database_fundamentals/acid_properties.py) for a practical demonstration using SQLAlchemy.

## Transaction Management

### Transaction States
```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Active  │────►│Partially │────►│Committed │
└──────────┘     │Committed │     └──────────┘
     │           └──────────┘          │
     │                                 │
     ▼                                 ▼
┌──────────┐                    ┌──────────┐
│  Failed  │                    │ Completed │
└──────────┘                    └──────────┘
```

### Concurrency Control

1. **Pessimistic Concurrency Control**
   - Locks resources before accessing
   - Prevents conflicts but reduces concurrency
   - Example: SELECT FOR UPDATE

2. **Optimistic Concurrency Control**
   - Allows concurrent access
   - Checks for conflicts at commit time
   - Example: Version numbers or timestamps

## Query Optimization

### Index Types
```
┌─────────────┐
│  B-Tree     │ - Balanced tree structure
│  Hash       │ - Direct key-value lookup
│  Bitmap     │ - For low-cardinality columns
│  GiST       │ - Geometric data
└─────────────┘
```

### Query Planning
1. Parse query
2. Create possible execution plans
3. Estimate cost of each plan
4. Choose lowest cost plan
5. Execute plan

## Best Practices

1. **Design**
   - Normalize data appropriately
   - Choose proper data types
   - Plan indexes carefully

2. **Implementation**
   - Use prepared statements
   - Implement proper error handling
   - Monitor performance

3. **Maintenance**
   - Regular backups
   - Index maintenance
   - Statistics updates 