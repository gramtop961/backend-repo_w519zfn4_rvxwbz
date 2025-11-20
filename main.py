import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timezone

from database import db
from bson import ObjectId

app = FastAPI(title="IndieStore API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------
# Helpers
# ----------------------

def to_str_id(doc: dict):
    if not doc:
        return doc
    d = {**doc}
    _id = d.get("_id")
    if isinstance(_id, ObjectId):
        d["id"] = str(_id)
        del d["_id"]
    return d

# ----------------------
# Models (request bodies)
# ----------------------

class ProductIn(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., ge=0, description="Price in INR")
    images: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    in_stock: bool = True
    rating: float = Field(4.5, ge=0, le=5)

class OrderItemIn(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1)
    price: float = Field(..., ge=0)

class OrderIn(BaseModel):
    items: List[OrderItemIn]
    customer_name: str
    customer_email: EmailStr
    address: str

# ----------------------
# Health
# ----------------------

@app.get("/health")
def health():
    ok = db is not None
    return {"status": "ok", "database": "connected" if ok else "unavailable"}

# ----------------------
# Products CRUD
# ----------------------

@app.get("/products")
def list_products(q: Optional[str] = None,
                  category: Optional[str] = None,
                  categories: Optional[str] = Query(None, description="Comma-separated list of categories")):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {}
    if q:
        filt["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    if category:
        filt["categories"] = {"$in": [category]}
    elif categories:
        cats = [c.strip() for c in categories.split(",") if c.strip()]
        if cats:
            filt["categories"] = {"$in": cats}
    docs = list(db["product"].find(filt).sort("created_at", -1))
    return [to_str_id(d) for d in docs]

@app.post("/products", status_code=201)
def create_product(prod: ProductIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    data = prod.model_dump()
    now = datetime.now(timezone.utc)
    data.update({"created_at": now, "updated_at": now})
    res = db["product"].insert_one(data)
    created = db["product"].find_one({"_id": res.inserted_id})
    return to_str_id(created)

@app.get("/products/{product_id}")
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")
    doc = db["product"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return to_str_id(doc)

@app.put("/products/{product_id}")
def update_product(product_id: str, prod: ProductIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")
    data = prod.model_dump()
    data["updated_at"] = datetime.now(timezone.utc)
    res = db["product"].update_one({"_id": oid}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    doc = db["product"].find_one({"_id": oid})
    return to_str_id(doc)

@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")
    res = db["product"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"ok": True}

# ----------------------
# Orders
# ----------------------

@app.post("/orders", status_code=201)
def create_order(order: OrderIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # compute total from items
    total = 0.0
    for it in order.items:
        total += it.price * it.quantity
    data = {
        "items": [i.model_dump() for i in order.items],
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "address": order.address,
        "status": "pending",
        "total": round(total, 2),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    res = db["order"].insert_one(data)
    created = db["order"].find_one({"_id": res.inserted_id})
    return to_str_id(created)

# ----------------------
# Seed data on startup
# ----------------------

@app.on_event("startup")
def seed_products():
    if db is None:
        return
    count = db["product"].count_documents({})
    if count > 0:
        return
    now = datetime.now(timezone.utc)
    products = [
        {
            "name": "Handcrafted Ceramic Vase",
            "description": "Minimalist matte white vase for modern homes",
            "price": 2499,
            "images": ["/images/vase.jpg"],
            "categories": ["Home Decor"],
            "in_stock": True,
            "rating": 4.6,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Bamboo Serving Tray",
            "description": "Sustainable tray with anti-slip base",
            "price": 1899,
            "images": ["/images/tray.jpg"],
            "categories": ["Kitchen"],
            "in_stock": True,
            "rating": 4.4,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Gold-Tone Hoop Earrings",
            "description": "Hypoallergenic, everyday wear",
            "price": 799,
            "images": ["/images/earrings.jpg"],
            "categories": ["Artificial Jewelry"],
            "in_stock": True,
            "rating": 4.5,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Orthopedic Pet Bed",
            "description": "Memory foam comfort for dogs and cats",
            "price": 3299,
            "images": ["/images/petbed.jpg"],
            "categories": ["Pet Supplies"],
            "in_stock": True,
            "rating": 4.7,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Copper Water Bottle",
            "description": "1L hammered copper, leak-proof",
            "price": 1599,
            "images": ["/images/bottle.jpg"],
            "categories": ["Health & Wellness"],
            "in_stock": True,
            "rating": 4.3,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Magnetic Cable Organizer",
            "description": "Keeps your desk tidy",
            "price": 499,
            "images": ["/images/cable.jpg"],
            "categories": ["Electronics"],
            "in_stock": True,
            "rating": 4.2,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Aromatic Soy Candle",
            "description": "Long-lasting sandalwood fragrance",
            "price": 699,
            "images": ["/images/candle.jpg"],
            "categories": ["Home Decor"],
            "in_stock": True,
            "rating": 4.1,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": 'Cast Iron Skillet 10"',
            "description": "Pre-seasoned, even heating",
            "price": 2299,
            "images": ["/images/skillet.jpg"],
            "categories": ["Kitchen"],
            "in_stock": True,
            "rating": 4.5,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Statement Necklace",
            "description": "Antique finish, lightweight",
            "price": 1299,
            "images": ["/images/necklace.jpg"],
            "categories": ["Artificial Jewelry"],
            "in_stock": True,
            "rating": 4.6,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Interactive Cat Teaser",
            "description": "Feather wand for active play",
            "price": 399,
            "images": ["/images/teaser.jpg"],
            "categories": ["Pet Supplies"],
            "in_stock": True,
            "rating": 4.0,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Copper Tongue Cleaner",
            "description": "Ayurvedic daily hygiene",
            "price": 249,
            "images": ["/images/tongue.jpg"],
            "categories": ["Health & Wellness"],
            "in_stock": True,
            "rating": 4.3,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "USB-C Fast Charger",
            "description": "25W compact adapter",
            "price": 1499,
            "images": ["/images/charger.jpg"],
            "categories": ["Electronics"],
            "in_stock": True,
            "rating": 4.4,
            "created_at": now,
            "updated_at": now,
        },
    ]
    if products:
        db["product"].insert_many(products)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
