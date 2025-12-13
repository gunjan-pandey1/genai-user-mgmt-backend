from fastapi import APIRouter, Body, Request, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List
from bson import ObjectId

from .models import UserCreate, UserUpdate, UserResponse
from .database import get_database

router = APIRouter()

@router.post("/", response_description="Add new user", response_model=UserResponse)
async def create_user(user: UserCreate = Body(...)):
    user_dict = jsonable_encoder(user)
    db = await get_database()
    new_user = await db["users"].insert_one(user_dict)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    return created_user

@router.get("/", response_description="List all users", response_model=List[UserResponse])
async def list_users(limit: int = 100):
    db = await get_database()
    users = await db["users"].find().to_list(limit)
    return users

@router.get("/{id}", response_description="Get a single user", response_model=UserResponse)
async def show_user(id: str):
    db = await get_database()
    if (user := await db["users"].find_one({"_id": ObjectId(id)})) is not None:
        return user
    raise HTTPException(status_code=404, detail=f"User {id} not found")

@router.put("/{id}", response_description="Update a user", response_model=UserResponse)
async def update_user(id: str, user: UserUpdate = Body(...)):
    db = await get_database()
    user_dict = {k: v for k, v in user.model_dump().items() if v is not None}

    if len(user_dict) >= 1:
        update_result = await db["users"].update_one({"_id": ObjectId(id)}, {"$set": user_dict})
        if update_result.modified_count == 1:
            if (updated_user := await db["users"].find_one({"_id": ObjectId(id)})) is not None:
                return updated_user

    if (existing_user := await db["users"].find_one({"_id": ObjectId(id)})) is not None:
        return existing_user

    raise HTTPException(status_code=404, detail=f"User {id} not found")

@router.delete("/{id}", response_description="Delete a user")
async def delete_user(id: str):
    db = await get_database()
    delete_result = await db["users"].delete_one({"_id": ObjectId(id)})

    if delete_result.deleted_count == 1:
        return {"message": "User deleted"}

    raise HTTPException(status_code=404, detail=f"User {id} not found")
