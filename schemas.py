from pydantic import BaseModel, HttpUrl
from typing import Optional


# Base Product 
class ProductBase(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None


# creating products
class ProductCreate(ProductBase):
    pass


# returning products
class Product(ProductBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True