from pydantic import BaseModel, Field
from typing import Literal

class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str
    description: str
    type: Literal["income", "expense"]

class TransactionResponse(BaseModel):
    id: int
    amount: float
    category: str
    description: str
    type: Literal["income", "expense"]
