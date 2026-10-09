from pydantic import BaseModel, Field, EmailStr
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


class TransactionSummary(BaseModel):
    total_income: float
    total_expenses: float
    balance: float


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: Literal["income", "expense"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
