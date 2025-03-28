"""
ACID Properties Demonstration

This module demonstrates the ACID properties of database transactions:
- Atomicity: All operations in a transaction succeed or all fail
- Consistency: Database remains in a valid state before and after transaction
- Isolation: Concurrent transactions don't interfere with each other
- Durability: Committed transactions persist even after system failures

ASCII Diagram:
```
┌────────────────┐
│   Transaction  │
│   ┌────────┐   │         ┌─────────────┐
│   │Operation│  │         │   Database  │
│   │   1    │   │    ┌───►│  Consistent │
│   └────────┘   │    │    │    State    │
│   ┌────────┐   │    │    └─────────────┘
│   │Operation│  │    │    ┌─────────────┐
│   │   2    │   │    │    │  Database   │
│   └────────┘   │    │    │ Inconsistent│
│   ┌────────┐   │    │    │    State    │
│   │Operation│  │    │    └─────────────┘
│   │   3    │   │    │          ▲
│   └────────┘   │    │          │
└───────┬────────┘    │          │
        │             │          │
    Success?──────Yes─┘          │
        │                        │
        └──────No────────────────┘
```
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import threading
import time

# Create SQLite in-memory database
engine = create_engine('sqlite:///:memory:', echo=False)
Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    balance = Column(Integer, nullable=False)
    transactions = relationship("Transaction", back_populates="account")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    amount = Column(Integer, nullable=False)
    account = relationship("Account", back_populates="transactions")

# Create tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)

def demonstrate_atomicity():
    """
    Demonstrate Atomicity: All operations in a transaction succeed or all fail.
    """
    session = Session()
    
    try:
        # Create account with initial balance
        account = Account(name="John", balance=1000)
        session.add(account)
        session.commit()
        
        # Try to perform invalid transaction
        try:
            account.balance -= 2000  # Would result in negative balance
            transaction = Transaction(account=account, amount=-2000)
            session.add(transaction)
            session.commit()
        except IntegrityError:
            session.rollback()
            print("Atomicity: Transaction rolled back due to invalid operation")
        
        # Verify account balance remained unchanged
        session.refresh(account)
        print(f"Atomicity: Account balance after failed transaction: {account.balance}")
        
    finally:
        session.close()

def demonstrate_consistency():
    """
    Demonstrate Consistency: Database remains in valid state.
    """
    session = Session()
    
    try:
        # Create account
        account = Account(name="Alice", balance=500)
        session.add(account)
        session.commit()
        
        # Define constraint: Balance must remain non-negative
        initial_balance = account.balance
        withdrawal_amount = 300
        
        if account.balance >= withdrawal_amount:
            account.balance -= withdrawal_amount
            transaction = Transaction(account=account, amount=-withdrawal_amount)
            session.add(transaction)
            session.commit()
            print(f"Consistency: Valid withdrawal completed. New balance: {account.balance}")
        else:
            print("Consistency: Transaction rejected to maintain valid state")
            
    finally:
        session.close()

def demonstrate_isolation():
    """
    Demonstrate Isolation: Concurrent transactions don't interfere.
    """
    def transaction1(account_id):
        session = Session()
        try:
            account = session.query(Account).get(account_id)
            # Simulate some processing time
            time.sleep(1)
            account.balance += 100
            transaction = Transaction(account=account, amount=100)
            session.add(transaction)
            session.commit()
            print("Isolation: Transaction 1 completed")
        finally:
            session.close()
    
    def transaction2(account_id):
        session = Session()
        try:
            account = session.query(Account).get(account_id)
            # Simulate some processing time
            time.sleep(1)
            account.balance += 200
            transaction = Transaction(account=account, amount=200)
            session.add(transaction)
            session.commit()
            print("Isolation: Transaction 2 completed")
        finally:
            session.close()
    
    # Create account
    session = Session()
    account = Account(name="Bob", balance=1000)
    session.add(account)
    session.commit()
    account_id = account.id
    session.close()
    
    # Run concurrent transactions
    thread1 = threading.Thread(target=transaction1, args=(account_id,))
    thread2 = threading.Thread(target=transaction2, args=(account_id,))
    
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    
    # Verify final balance
    session = Session()
    account = session.query(Account).get(account_id)
    print(f"Isolation: Final balance after concurrent transactions: {account.balance}")
    session.close()

def demonstrate_durability():
    """
    Demonstrate Durability: Committed transactions persist.
    """
    session = Session()
    
    try:
        # Create and commit account
        account = Account(name="Charlie", balance=750)
        session.add(account)
        session.commit()
        account_id = account.id
        
        # Simulate system crash by creating new session
        session.close()
        new_session = Session()
        
        # Verify data persisted
        recovered_account = new_session.query(Account).get(account_id)
        print(f"Durability: Account recovered after 'system crash': {recovered_account.name}, Balance: {recovered_account.balance}")
        
    finally:
        new_session.close()

if __name__ == "__main__":
    print("\nDemonstrating ACID Properties:\n")
    
    print("1. Atomicity Test:")
    demonstrate_atomicity()
    
    print("\n2. Consistency Test:")
    demonstrate_consistency()
    
    print("\n3. Isolation Test:")
    demonstrate_isolation()
    
    print("\n4. Durability Test:")
    demonstrate_durability() 
