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

# --- Seed sample products on startup if empty ---
@app.on_event("startup")
async def seed_products():
    existing = await get_documents("product", {}, 1)
    if existing:
        return

    samples: List[ProductCreate] = [
        # Home Decor
        ProductCreate(
            name="Handwoven Cotton Throw",
            description="Soft, breathable throw with subtle texture for modern living rooms.",
            price=49.00,
            images=[
                "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["home decor"],
            in_stock=True,
            rating=4.6,
        ),
        ProductCreate(
            name="Minimalist Ceramic Vase",
            description="Matte stoneware vase for fresh or dried floral arrangements.",
            price=39.00,
            images=[
                "https://images.unsplash.com/photo-1549187774-b4e9b0445b41?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["home decor"],
            in_stock=True,
            rating=4.4,
        ),
        # Kitchen
        ProductCreate(
            name="Acacia Wood Cutting Board",
            description="Durable, knife-friendly board with juice groove.",
            price=29.00,
            images=[
                "https://images.unsplash.com/photo-1515548212307-6f2b1e3c0f51?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["kitchen"],
            in_stock=True,
            rating=4.7,
        ),
        ProductCreate(
            name="Double‑Wall Glass Mug (2pc)",
            description="Insulated borosilicate mugs for coffee and tea.",
            price=24.00,
            images=[
                "https://images.unsplash.com/photo-1497636577773-f1231844b336?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["kitchen"],
            in_stock=True,
            rating=4.5,
        ),
        # Artificial Jewelry
        ProductCreate(
            name="Gold‑Tone Huggie Hoops",
            description="Hypoallergenic stainless steel with 18k gold tone finish.",
            price=19.00,
            images=[
                "https://images.unsplash.com/photo-1490114538077-0a7f8cb49891?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["artificial jewelry"],
            in_stock=True,
            rating=4.3,
        ),
        ProductCreate(
            name="Pearl Drop Necklace",
            description="Elegant freshwater‑style pendant on a fine chain.",
            price=22.00,
            images=[
                "https://images.unsplash.com/photo-1603565816278-c5c9a0a1f9de?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["artificial jewelry"],
            in_stock=True,
            rating=4.2,
        ),
        # Pet Supplies
        ProductCreate(
            name="Memory Foam Pet Bed",
            description="Washable cover, non‑slip base, supportive foam.",
            price=59.00,
            images=[
                "https://images.unsplash.com/photo-1558944351-cf21b4f99f05?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["pet supplies"],
            in_stock=True,
            rating=4.6,
        ),
        ProductCreate(
            name="Silicone Slow Feeder Bowl",
            description="Promotes healthier eating pace for dogs and cats.",
            price=18.00,
            images=[
                "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["pet supplies"],
            in_stock=True,
            rating=4.4,
        ),
        # Health and Wellness
        ProductCreate(
            name="Stainless Steel Water Bottle (750ml)",
            description="Vacuum insulated, keeps drinks cold 24h or hot 12h.",
            price=27.00,
            images=[
                "https://images.unsplash.com/photo-1592167940413-8d743a6c0f36?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["health and wellness"],
            in_stock=True,
            rating=4.8,
        ),
        ProductCreate(
            name="Cork Yoga Block (2pc)",
            description="High‑density natural cork for stability and grip.",
            price=23.00,
            images=[
                "https://images.unsplash.com/photo-1588286840104-8957b019727f?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["health and wellness"],
            in_stock=True,
            rating=4.5,
        ),
        # Electronics
        ProductCreate(
            name="Wireless Charging Pad",
            description="Qi‑compatible, slim profile with soft‑touch finish.",
            price=28.00,
            images=[
                "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["electronics"],
            in_stock=True,
            rating=4.4,
        ),
        ProductCreate(
            name="Noise‑Isolating Earbuds",
            description="Comfortable fit, balanced sound, inline mic.",
            price=34.00,
            images=[
                "https://images.unsplash.com/photo-1518443881240-4e00f9b11669?q=80&w=1200&auto=format&fit=crop",
            ],
            categories=["electronics"],
            in_stock=True,
            rating=4.3,
        ),
    ]

    for s in samples:
        await create_document("product", s.model_dump())

# Products Endpoints
@app.post("/products", response_model=Product)
async def create_product(product: ProductCreate):
    data = product.model_dump()
    doc = await create_document("product", data)
    if not doc:
        raise HTTPException(status_code=500, detail="Failed to create product")
    return Product(**doc)

@app.get("/products", response_model=List[Product])
async def list_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    categories: Optional[str] = None,
    limit: int = 50,
):
    filter_parts = []
    if q:
        filter_parts.append({"name": {"$regex": q, "$options": "i"}})
    if category:
        filter_parts.append({"categories": category})
    if categories:
        cats = [c.strip() for c in categories.split(",") if c.strip()]
        if cats:
            filter_parts.append({"categories": {"$in": cats}})

    if not filter_parts:
        filter_dict = {}
    elif len(filter_parts) == 1:
        filter_dict = filter_parts[0]
    else:
        filter_dict = {"$and": filter_parts}

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
