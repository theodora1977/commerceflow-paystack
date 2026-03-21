from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Product as ProductModel
from schemas import Product, ProductCreate

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# Get all products
@router.get("/", response_model=List[Product], response_model_exclude_none=True)
def get_products(db: Session = Depends(get_db)):
    products = db.query(ProductModel).all()
    return products


# Get a single product
@router.get("/{product_id}", response_model=Product, response_model_exclude_none=True)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


# Create a new product
@router.post("/", response_model=Product, response_model_exclude_none=True)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    new_product = ProductModel(**product.dict())

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product