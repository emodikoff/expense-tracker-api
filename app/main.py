from fastapi import FastAPI

from app.routers import auth, categories, transactions, analytics

app = FastAPI()

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(analytics.router)
app.include_router(transactions.router)


@app.get("/")
def root():
    return {"message": "ExpenseTracker API is running"}
