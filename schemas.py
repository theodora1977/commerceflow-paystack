from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

class CartItem(BaseModel):
    id: int
    qty: int

class PaymentInitRequest(BaseModel):
    email: str
    amount: int
    product_id: Optional[int] = None
    cart_items: Optional[List[CartItem]] = None
    metadata: Optional[dict] = None

class PaymentInitResponse(BaseModel):
    message: str
    authorization_url: str
    reference: str

class PaymentVerifyResponse(BaseModel):
    message: str
    status: str
    reference: str
    amount: str
    email: str

class OrderOut(BaseModel):
    id: int
    email: str
    amount: float
    reference: str
    status: str
    product_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
