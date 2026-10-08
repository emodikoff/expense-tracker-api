from pydantic import BaseModel
from typing import Literal

class Transaction(BaseModel):
    amount: float
    category: str
    description: str
    type: Literal["income", "expense"]
