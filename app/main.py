"""
Keroxio API v2 - Unified Backend
Consolidates: auth, gateway, billing, subscription, crm, email, notification
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.modules.auth.router import router as auth_router
from app.modules.billing.router import router as billing_router
from app.modules.subscription.router import router as subscription_router
from app.modules.crm.router import router as crm_router
from app.modules.email.router import router as email_router
from app.modules.notification.router import router as notification_router
from app.modules.pricing.router import router as pricing_router
from app.modules.immat.router import router as immat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Keroxio API",
    description="Plateforme d'aide à la vente automobile",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/")
async def root():
    return {
        "name": "Keroxio API",
        "version": "2.0.0",
        "modules": ["auth", "billing", "subscription", "crm", "email", "notification"]
    }


# Mount routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(billing_router, prefix="/billing", tags=["Billing"])
app.include_router(subscription_router, prefix="/subscription", tags=["Subscription"])
app.include_router(crm_router, prefix="/crm", tags=["CRM"])
app.include_router(email_router, prefix="/email", tags=["Email"])
app.include_router(notification_router, prefix="/notification", tags=["Notification"])
app.include_router(pricing_router, prefix="/pricing", tags=["Pricing"])
app.include_router(immat_router, prefix="/immat", tags=["Immatriculation"])
