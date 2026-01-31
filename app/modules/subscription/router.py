"""
Subscription module - manages user subscriptions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import stripe

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user
from app.modules.subscription.models import Subscription

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    status: str
    current_period_end: Optional[datetime]
    
    class Config:
        from_attributes = True


@router.get("/current", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's current subscription"""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user["id"])
        .where(Subscription.status == "active")
    )
    subscription = result.scalar_one_or_none()
    return subscription


@router.get("/usage")
async def get_usage(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's usage stats for current billing period"""
    # TODO: Calculate actual usage from database
    return {
        "annonces_created": 3,
        "annonces_limit": 5,  # Free tier
        "images_processed": 2,
        "api_calls": 47,
        "period_start": "2026-01-01",
        "period_end": "2026-01-31"
    }


@router.post("/cancel")
async def cancel_subscription(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel current subscription"""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user["id"])
        .where(Subscription.status == "active")
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription")
    
    # Cancel in Stripe
    if subscription.stripe_subscription_id and settings.STRIPE_SECRET_KEY:
        try:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Update local status
    subscription.status = "cancelled"
    await db.commit()
    
    return {"message": "Subscription cancelled", "ends_at": subscription.current_period_end}


@router.post("/resume")
async def resume_subscription(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resume a cancelled subscription (if still in grace period)"""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user["id"])
        .where(Subscription.status == "cancelled")
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No cancelled subscription to resume")
    
    # Check if still in grace period
    if subscription.current_period_end and subscription.current_period_end < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Grace period expired, please create a new subscription")
    
    # Resume in Stripe
    if subscription.stripe_subscription_id and settings.STRIPE_SECRET_KEY:
        try:
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=False
            )
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    subscription.status = "active"
    await db.commit()
    
    return {"message": "Subscription resumed"}
