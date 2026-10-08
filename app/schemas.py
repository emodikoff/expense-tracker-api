from pydantic import BaseModel, Field
from typing import Literal

class Transaction(BaseModel):
    amount: float = Field(gt=0)
    category: str
    description: str
    type: Literal["income", "expense"]
