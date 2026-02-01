"""
Auth module - handles authentication and user management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_db
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_user
)
from app.modules.auth.models import User

router = APIRouter()


# Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    
    class Config:
        from_attributes = True


# Endpoints
@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        name=user_data.name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Generate token
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access token"""
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/logout")
async def logout():
    """Logout (client should discard token)"""
    return {"message": "Logged out successfully"}


@router.post("/admin/set-role")
async def set_user_role(
    email: str,
    role: str,
    admin_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Set user role (admin only) and create subscription if pro"""
    from app.modules.subscription.models import Subscription
    from datetime import datetime, timedelta
    
    # Simple admin key check
    if admin_key != "keroxio-admin-2026":
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    if role not in ["user", "pro", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role
    
    # If pro, create a subscription
    if role == "pro":
        # Check for existing subscription
        sub_result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        existing_sub = sub_result.scalar_one_or_none()
        
        if existing_sub:
            existing_sub.plan = "pro"
            existing_sub.status = "active"
            existing_sub.current_period_start = datetime.utcnow()
            existing_sub.current_period_end = datetime.utcnow() + timedelta(days=365)
        else:
            subscription = Subscription(
                user_id=user.id,
                plan="pro",
                status="active",
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=365)
            )
            db.add(subscription)
    
    await db.commit()
    
    return {"message": f"User {email} role set to {role}", "subscription": role == "pro"}
