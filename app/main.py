from fastapi import FastAPI, Depends, HTTPException
from app.schemas import TransactionCreate, TransactionResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transaction as TransactionModel

app = FastAPI()

@app.get("/")
def root():
    return {"message": "ExpenseTracker API is running"}

@app.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(db: Session = Depends(get_db)):
    return db.query(TransactionModel).all()

@app.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
        transaction_id: int,
        db: Session = Depends(get_db),
):
    db_transaction = (
        db.query(TransactionModel)
        .filter(TransactionModel.id == transaction_id)
        .first()
    )

    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return db_transaction

@app.post("/transactions", response_model=TransactionResponse)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
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
