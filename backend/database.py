import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel

MONGO_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "indie_store")

client = AsyncIOMotorClient(MONGO_URL)
db: AsyncIOMotorDatabase = client[DB_NAME]

async def create_document(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow()
    data["created_at"] = now
    data["updated_at"] = now
    result = await db[collection_name].insert_one(data)
    doc = await db[collection_name].find_one({"_id": result.inserted_id})
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc or {}

async def get_documents(
    collection_name: str,
    filter_dict: Optional[Dict[str, Any]] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    filter_dict = filter_dict or {}
    cursor = db[collection_name].find(filter_dict).limit(limit)
    docs = []
    async for d in cursor:
        d["id"] = str(d.pop("_id"))
        docs.append(d)
    return docs

async def get_document(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    from bson import ObjectId
    try:
        oid = ObjectId(doc_id)
    except Exception:
        return None
    doc = await db[collection_name].find_one({"_id": oid})
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc

async def update_document(collection_name: str, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    from bson import ObjectId
    try:
        oid = ObjectId(doc_id)
    except Exception:
        return None
    data["updated_at"] = datetime.utcnow()
    await db[collection_name].update_one({"_id": oid}, {"$set": data})
    return await get_document(collection_name, doc_id)

async def delete_document(collection_name: str, doc_id: str) -> bool:
    from bson import ObjectId
    try:
        oid = ObjectId(doc_id)
    except Exception:
        return False
    res = await db[collection_name].delete_one({"_id": oid})
    return res.deleted_count == 1
