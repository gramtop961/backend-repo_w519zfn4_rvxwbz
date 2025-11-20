from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from schemas import ProductCreate, Product, OrderCreate, Order
from database import (
    create_document,
    get_documents,
    get_document,
    update_document,
    delete_document,
)

app = FastAPI(title="IndieStore API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to IndieStore API"}

# Products Endpoints
@app.post("/products", response_model=Product)
async def create_product(product: ProductCreate):
    data = product.model_dump()
    doc = await create_document("product", data)
    if not doc:
        raise HTTPException(status_code=500, detail="Failed to create product")
    return Product(**doc)

@app.get("/products", response_model=List[Product])
async def list_products(q: Optional[str] = None, limit: int = 50):
    filter_dict = {}
    if q:
        # Simple case-insensitive search on name
        filter_dict = {"name": {"$regex": q, "$options": "i"}}
    docs = await get_documents("product", filter_dict, limit)
    return [Product(**d) for d in docs]

@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    doc = await get_document("product", product_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**doc)

@app.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product: ProductCreate):
    doc = await update_document("product", product_id, product.model_dump())
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**doc)

@app.delete("/products/{product_id}")
async def delete_product(product_id: str):
    ok = await delete_document("product", product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "deleted"}

# Orders Endpoints
@app.post("/orders", response_model=Order)
async def create_order(order: OrderCreate):
    data = order.model_dump()
    total = sum(item.price * item.quantity for item in order.items)
    data["total"] = total
    doc = await create_document("order", data)
    if not doc:
        raise HTTPException(status_code=500, detail="Failed to create order")
    return Order(**doc)

@app.get("/orders", response_model=List[Order])
async def list_orders(limit: int = 50):
    docs = await get_documents("order", {}, limit)
    return [Order(**d) for d in docs]

@app.get("/health")
async def health():
    return {"status": "ok"}
