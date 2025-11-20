from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

# Product schema defines the structure for products in the "product" collection
class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: float = Field(..., gt=0)
    images: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    in_stock: bool = True
    rating: float = Field(default=0, ge=0, le=5)

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Order schema defines the structure for orders in the "order" collection
class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)

class OrderCreate(BaseModel):
    items: List[OrderItem]
    customer_name: str
    customer_email: str
    address: str
    status: str = "pending"

class Order(OrderCreate):
    id: str
    created_at: datetime
    updated_at: datetime
