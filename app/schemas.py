from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Literal
from datetime import date
from decimal import Decimal

class TransactionCreate(BaseModel):
    amount: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )
    category: str | None = None
    category_id: int | None = Field(default=None, gt=0)
    description: str
    type: Literal["income", "expense"]
    transaction_date: date | None = None

    @model_validator(mode="after")
    def validate_category(self):
        if self.category_id is None:
            if self.category is None or not self.category.strip():
                raise ValueError(
                    "Either category or category_id must be provided"
                )

        return self


class TransactionResponse(BaseModel):
    id: int
    amount: Decimal
    category: str
    category_id: int | None
    description: str
    type: Literal["income", "expense"]
    transaction_date: date | None


class TransactionSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal


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


class MonthlyTransactionSummary(BaseModel):
    year: int
    month: int
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal


class CategoryExpenseSummary(BaseModel):
    category: str
    total: Decimal


class MonthlyCategoryExpenseSummary(BaseModel):
    year: int
    month: int
    total_expenses: Decimal
    categories: list[CategoryExpenseSummary]
