from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Literal


class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str
    category_id: int | None = Field(default=None, gt=0)
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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    type: Literal["income", "expense"]

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()

        if not name:
            raise ValueError("Category name cannot be empty")

        return name
