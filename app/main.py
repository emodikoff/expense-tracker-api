from fastapi import FastAPI, Depends
from app.schemas import Transaction
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transaction as TransactionModel

app = FastAPI()

transactions = [
    {
        "id": 1,
        "amount": 25.50,
        "category": "Food",
        "description": "Lunch",
        "type": "expense"
    },
    {
        "id": 2,
        "amount": 1200.00,
        "category": "Salary",
        "description": "Monthly salary",
        "type": "income"
    }
]

@app.get("/")
def root():
    return {"message": "ExpenseTracker API is running"}

@app.get("/transactions", response_model=list[Transaction])
def get_transactions(db: Session = Depends(get_db)):
    return db.query(TransactionModel).all()

@app.post("/transactions", response_model=Transaction)
def create_transaction(transaction: Transaction, db: Session = Depends(get_db)):
    db_transaction = TransactionModel(
        amount=transaction.amount,
        category=transaction.category,
        description=transaction.description,
        type=transaction.type,
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction
