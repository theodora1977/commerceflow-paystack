from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class Order(Base):
    """
    Represents a customer transaction in the system.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    amount = Column(Float)
    reference = Column(String, unique=True, index=True)
    status = Column(String, default="pending")  # pending, success, failed, abandoned
    product_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())