"""
Database Schemas

IndieStore MongoDB collection schemas using Pydantic models.
Each Pydantic model represents a collection in your database.
Collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product"
    """
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in INR (rupees)")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    categories: List[str] = Field(default_factory=list, description="Product categories")
    in_stock: bool = Field(True, description="Availability")
    rating: float = Field(4.5, ge=0, le=5, description="Average rating")

class OrderItem(BaseModel):
    product_id: str = Field(..., description="Referenced product id")
    quantity: int = Field(..., ge=1, description="Quantity of the item")
    price: float = Field(..., ge=0, description="Unit price captured at checkout (INR)")

class Order(BaseModel):
    """
    Orders collection schema
    Collection name: "order"
    """
    items: List[OrderItem] = Field(..., description="Line items")
    customer_name: str = Field(..., description="Customer full name")
    customer_email: EmailStr = Field(..., description="Customer email")
    address: str = Field(..., description="Shipping address")
    status: str = Field("pending", description="Order status")
    total: float = Field(..., ge=0, description="Computed grand total in INR")
