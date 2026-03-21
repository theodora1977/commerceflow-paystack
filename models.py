from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


# -----------------------------
# PRODUCT MODEL
# -----------------------------
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    image_url = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


# -----------------------------
# ORDER MODEL
# -----------------------------
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, paid, failed

    created_at = Column(DateTime, default=datetime.utcnow)

    # relationship
    items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", back_populates="order", uselist=False)


# -----------------------------
# ORDER ITEM MODEL
# -----------------------------
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    quantity = Column(Integer, nullable=False)

    # relationships
    order = relationship("Order", back_populates="items")


# -----------------------------
# PAYMENT MODEL
# -----------------------------
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("orders.id"))
    reference = Column(String, unique=True, index=True)

    amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, success, failed

    created_at = Column(DateTime, default=datetime.utcnow)

    # relationship
    order = relationship("Order", back_populates="payment")