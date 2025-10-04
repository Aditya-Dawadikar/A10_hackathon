import os
from typing import List, Optional, Union
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load env
load_dotenv()
# MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGODB_DBNAME")
username = os.getenv("MONGODB_USERNAME")
password = os.getenv("MONGODB_PASSWORD")
MONGO_URI = f"mongodb+srv://{username}:{password}@a10-hackathon.hmpirgq.mongodb.net/?retryWrites=true&w=majority&appName=A10-hackathon"


# Mongo client
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
policies_collection = db["policies"]
groups_collection = db["groups"]

# ---------- Pydantic Models ----------
class PolicyIn(BaseModel):
    name: str
    pattern: str
    replacement: str
    active: bool = True

class PolicyOut(PolicyIn):
    id: str

class GroupIn(BaseModel):
    name: str

class GroupOut(BaseModel):
    id: str
    name: str
    policy_ids: List[str] = []

# ---------- Policy CRUD ----------
async def create_policy(policy: PolicyIn) -> PolicyOut:
    doc = policy.dict()
    result = await policies_collection.insert_one(doc)
    return PolicyOut(id=str(result.inserted_id), **doc)

async def get_policy(policy_id: str) -> Optional[PolicyOut]:
    doc = await policies_collection.find_one({"_id": ObjectId(policy_id)})
    if not doc:
        return None
    return PolicyOut(id=str(doc["_id"]), **doc)

async def list_policies() -> List[PolicyOut]:
    results = []
    async for doc in policies_collection.find():
        results.append(PolicyOut(id=str(doc["_id"]), **doc))
    return results

async def update_policy(policy_id: str, policy: PolicyIn) -> Optional[PolicyOut]:
    await policies_collection.update_one(
        {"_id": ObjectId(policy_id)}, {"$set": policy.dict()}
    )
    doc = await policies_collection.find_one({"_id": ObjectId(policy_id)})
    if not doc:
        return None
    return PolicyOut(id=str(doc["_id"]), **doc)

async def delete_policy(policy_id: str) -> bool:
    result = await policies_collection.delete_one({"_id": ObjectId(policy_id)})
    return result.deleted_count > 0

# ---------- Group CRUD ----------
async def create_group(group: GroupIn) -> GroupOut:
    doc = {"name": group.name, "policy_ids": []}
    result = await groups_collection.insert_one(doc)
    return GroupOut(id=str(result.inserted_id), **doc)

async def get_group(group_id: str) -> Optional[GroupOut]:
    doc = await groups_collection.find_one({"_id": ObjectId(group_id)})
    if not doc:
        return None
    return GroupOut(id=str(doc["_id"]), name=doc["name"], policy_ids=doc.get("policy_ids", []))

async def list_groups() -> List[GroupOut]:
    results = []
    async for doc in groups_collection.find():
        results.append(GroupOut(id=str(doc["_id"]), name=doc["name"], policy_ids=doc.get("policy_ids", [])))
    return results

async def update_group(group_id: str, name: str) -> Optional[GroupOut]:
    await groups_collection.update_one({"_id": ObjectId(group_id)}, {"$set": {"name": name}})
    doc = await groups_collection.find_one({"_id": ObjectId(group_id)})
    if not doc:
        return None
    return GroupOut(id=str(doc["_id"]), name=doc["name"], policy_ids=doc.get("policy_ids", []))

async def delete_group(group_id: str) -> bool:
    result = await groups_collection.delete_one({"_id": ObjectId(group_id)})
    return result.deleted_count > 0

# ---------- Group ↔ Policy Management ----------
async def add_policy_to_group(group_id: str, policy_id: str) -> Optional[GroupOut]:
    await groups_collection.update_one(
        {"_id": ObjectId(group_id)},
        {"$addToSet": {"policy_ids": policy_id}}
    )
    return await get_group(group_id)

async def remove_policy_from_group(group_id: str, policy_id: str) -> Optional[GroupOut]:
    await groups_collection.update_one(
        {"_id": ObjectId(group_id)},
        {"$pull": {"policy_ids": policy_id}}
    )
    return await get_group(group_id)

async def get_group_with_policies(group_id: str = None, name: str = None):
    query = {}
    if group_id:
        query = {"_id": ObjectId(group_id)}
    elif name:
        query = {"name": {"$regex": f"^{name}$", "$options": "i"}}
    else:
        return None

    # Fetch group
    doc = await groups_collection.find_one(query)
    if not doc:
        return None

    # Expand policies
    policies = []
    for pid in doc.get("policy_ids", []):
        p = await policies_collection.find_one({"_id": ObjectId(pid)})
        if p:
            policies.append({
                "id": str(p["_id"]),
                "name": p["name"],
                "pattern": p["pattern"],
                "replacement": p["replacement"],
                "active": p["active"]
            })

    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "policies": policies
    }

async def get_all_groups_with_policies():
    groups = []
    cursor = groups_collection.find({})

    async for doc in cursor:
        # Expand policies for this group
        policies = []
        for pid in doc.get("policy_ids", []):
            p = await policies_collection.find_one({"_id": ObjectId(pid)})
            if p:
                policies.append({
                    "id": str(p["_id"]),
                    "name": p["name"],
                    "pattern": p["pattern"],
                    "replacement": p["replacement"],
                    "active": p["active"]
                })

        groups.append({
            "id": str(doc["_id"]),
            "name": doc["name"],
            "policies": policies
        })

    return groups

async def update_group_policies(group_id: str, policy_ids: List[str]):
    await groups_collection.update_one(
        {"_id": ObjectId(group_id)},
        {"$set": {"policy_ids": policy_ids}}
    )
    return await get_group_with_policies(group_id=group_id)