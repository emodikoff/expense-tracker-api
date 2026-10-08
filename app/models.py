from sqlalchemy import Column, Integer, String, Numeric
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10,2), nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    type = Column(String, nullable=False)
