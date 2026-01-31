"""
Billing module - Stripe payments
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import stripe

from app.core.config import settings
from app.core.security import get_current_user

router = APIRouter()

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSession(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class PaymentIntentRequest(BaseModel):
    amount: int  # in cents
    currency: str = "eur"


@router.post("/create-checkout-session")
async def create_checkout_session(
    data: CreateCheckoutSession,
    current_user: dict = Depends(get_current_user)
):
    """Create a Stripe checkout session"""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": data.price_id, "quantity": 1}],
            mode="subscription",
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            client_reference_id=current_user["id"],
            customer_email=current_user.get("email"),
        )
        return {"session_id": session.id, "url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-payment-intent")
async def create_payment_intent(
    data: PaymentIntentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a payment intent for one-time payments"""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=data.amount,
            currency=data.currency,
            metadata={"user_id": current_user["id"]}
        )
        return {"client_secret": intent.client_secret}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # TODO: Update user subscription status
        print(f"Checkout completed for user: {session.get('client_reference_id')}")
    
    elif event["type"] == "invoice.paid":
        invoice = event["data"]["object"]
        print(f"Invoice paid: {invoice['id']}")
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        # TODO: Cancel user subscription
        print(f"Subscription cancelled: {subscription['id']}")
    
    return {"status": "success"}


@router.get("/plans")
async def get_plans():
    """Get available pricing plans"""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Gratuit",
                "price": 0,
                "features": ["5 annonces/mois", "Estimation de prix", "Support email"]
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 29,
                "price_id": "price_pro_monthly",  # Replace with actual Stripe price ID
                "features": ["Annonces illimitées", "Nettoyage d'images", "Priorité support", "API access"]
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": 99,
                "price_id": "price_enterprise_monthly",
                "features": ["Tout Pro +", "Multi-utilisateurs", "Intégration LeBonCoin", "Account manager"]
            }
        ]
    }
