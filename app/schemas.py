from pydantic import BaseModel

class Transaction(BaseModel):
    amount: float
    category: str
    description: str
    type: str