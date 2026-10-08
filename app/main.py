from fastapi import FastAPI
from app.schemas import Transaction

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
def get_transactions():
    return transactions

@app.post("/transactions", response_model=Transaction)
def create_transaction(transaction: Transaction):
    transactions.append(transaction)
    return transaction