from fastapi import APIRouter, HTTPException
from models import UserSignup, UserLogin
from database import users_collection
from auth import hash_password, verify_password, create_access_token
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
async def signup(user: UserSignup):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    result = await users_collection.insert_one({
        "email": user.email,
        "password": hashed,
        "name": user.name
    })
    token = create_access_token({"sub": str(result.inserted_id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login")
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(db_user["_id"])})
    return {"access_token": token, "token_type": "bearer"}