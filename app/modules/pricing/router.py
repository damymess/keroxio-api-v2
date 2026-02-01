"""Pricing router - Vehicle price estimation endpoints"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()

# === Schemas ===
class EstimationRequest(BaseModel):
    brand: str
    model: str
    year: int = Field(..., ge=1990, le=2030)
    mileage: int = Field(..., ge=0)
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    condition: Optional[str] = "good"

class EstimationResponse(BaseModel):
    estimated_price: int
    price_min: int
    price_max: int
    confidence: float
    market_position: str
    factors: Dict[str, Any] = {}
    recommendations: List[str] = []

# === Pricing Engine ===
BRAND_TIERS = {
    "premium": ["audi", "bmw", "mercedes", "volvo", "porsche", "tesla"],
    "mid": ["volkswagen", "toyota", "honda", "mazda", "skoda", "hyundai", "kia", "ford"],
    "economy": ["dacia", "fiat", "seat", "opel", "citroen", "peugeot", "renault", "nissan"],
}

DEPRECIATION = {0: 1.0, 1: 0.80, 2: 0.70, 3: 0.60, 4: 0.52, 5: 0.45, 
                6: 0.40, 7: 0.35, 8: 0.31, 9: 0.28, 10: 0.25, 15: 0.15, 20: 0.10}

def get_base_price(brand: str, model: str) -> int:
    brand_lower = brand.lower()
    for tier, brands in BRAND_TIERS.items():
        if brand_lower in brands:
            return {"premium": 45000, "mid": 32000, "economy": 25000}[tier]
    return 28000

def get_depreciation(age: int) -> float:
    if age <= 0: return 1.0
    if age >= 20: return 0.10
    for a in sorted(DEPRECIATION.keys(), reverse=True):
        if age >= a: return DEPRECIATION[a]
    return 0.10

def estimate_price(req: EstimationRequest) -> dict:
    age = datetime.now().year - req.year
    base = get_base_price(req.brand, req.model)
    price = base * get_depreciation(age)
    
    # Mileage adjustment
    expected_km = age * 15000
    km_diff = (req.mileage - expected_km) / 10000
    price *= max(0.7, min(1.15, 1.0 - km_diff * 0.02))
    
    # Fuel adjustment
    fuel_mult = {"electric": 1.15, "hybrid": 1.08, "diesel": 0.95}.get(
        (req.fuel_type or "").lower(), 1.0)
    price *= fuel_mult
    
    # Condition
    cond_mult = {"excellent": 1.10, "good": 1.0, "fair": 0.90, "poor": 0.75}.get(
        (req.condition or "good").lower(), 1.0)
    price *= cond_mult
    
    price = round(price / 100) * 100
    return {
        "price": int(price),
        "price_min": int(price * 0.92),
        "price_max": int(price * 1.08),
        "confidence": 0.80,
        "market_position": "average",
        "factors": {"base_price": base, "age": age, "depreciation": round((1-get_depreciation(age))*100, 1)},
        "recommendations": ["Prix cohérent avec le marché"]
    }

# === Endpoints ===
@router.post("/estimate", response_model=EstimationResponse)
async def estimate_vehicle(request: EstimationRequest):
    """Estimate vehicle price"""
    result = estimate_price(request)
    return EstimationResponse(
        estimated_price=result["price"],
        price_min=result["price_min"],
        price_max=result["price_max"],
        confidence=result["confidence"],
        market_position=result["market_position"],
        factors=result["factors"],
        recommendations=result["recommendations"]
    )

@router.get("/brands")
async def get_brands():
    """Get supported brands"""
    brands = set()
    for tier_brands in BRAND_TIERS.values():
        brands.update(b.title() for b in tier_brands)
    return {"brands": sorted(brands)}
