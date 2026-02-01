"""Immat router - Vehicle lookup by registration plate"""
from fastapi import APIRouter, HTTPException, Path, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import re
import os

from .ocr import read_plate_from_image, PlateOCRResult

router = APIRouter()

PLATE_RECOGNIZER_API_KEY = os.getenv("PLATE_RECOGNIZER_API_KEY", "")

# === Schemas ===
class VehicleInfo(BaseModel):
    plaque: str
    marque: Optional[str] = None
    modele: Optional[str] = None
    version: Optional[str] = None
    type_carburant: Optional[str] = None
    puissance_fiscale: Optional[int] = None
    premiere_immat_year: Optional[int] = None
    data_source: str = "plate_format"

class LookupResponse(BaseModel):
    success: bool
    vehicle: Optional[VehicleInfo] = None
    source: str = "minimal"
    error: Optional[str] = None

# === Helpers ===
def validate_plate(plaque: str) -> str:
    """Validate and normalize French plate"""
    plaque = plaque.upper().replace(" ", "").replace("-", "")
    
    # New format: AA-123-BB
    if re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$', plaque):
        return f"{plaque[:2]}-{plaque[2:5]}-{plaque[5:]}"
    
    # Old format: 123 ABC 75
    if re.match(r'^\d{1,4}[A-Z]{1,3}\d{2,3}$', plaque):
        return plaque
    
    raise ValueError("Format de plaque invalide")

def estimate_year_from_plate(plaque: str) -> Optional[int]:
    """Estimate registration year from new format plate"""
    match = re.match(r'^([A-Z]{2})-?\d{3}-?[A-Z]{2}$', plaque)
    if match:
        first_letter = match.group(1)[0]
        year = 2009 + (ord(first_letter) - ord('A')) * 2
        if year <= datetime.now().year:
            return year
    return None

def lookup_vehicle(plaque: str) -> VehicleInfo:
    """Look up vehicle info (minimal implementation)"""
    year = estimate_year_from_plate(plaque)
    return VehicleInfo(
        plaque=plaque,
        premiere_immat_year=year,
        data_source="plate_format"
    )

# === Endpoints ===
@router.get("/{plaque}", response_model=LookupResponse)
async def lookup_by_plate(
    plaque: str = Path(..., min_length=7, max_length=12, description="Numéro d'immatriculation")
):
    """Look up vehicle by plate number"""
    try:
        plaque = validate_plate(plaque)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    vehicle = lookup_vehicle(plaque)
    return LookupResponse(
        success=True,
        vehicle=vehicle,
        source="minimal"
    )

@router.post("/search", response_model=LookupResponse)
async def search_plate(request: dict):
    """Search vehicle by plate (POST)"""
    plaque = request.get("plaque", "")
    try:
        plaque = validate_plate(plaque)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    vehicle = lookup_vehicle(plaque)
    return LookupResponse(
        success=True,
        vehicle=vehicle,
        source="minimal"
    )

@router.get("/{plaque}/validate")
async def validate_plate_endpoint(plaque: str):
    """Validate a plate number format"""
    try:
        normalized = validate_plate(plaque)
        return {"valid": True, "normalized": normalized}
    except ValueError:
        return {"valid": False, "normalized": None}

# === OCR Endpoints ===
@router.post("/ocr", response_model=PlateOCRResult)
async def ocr_plate(file: UploadFile = File(...)):
    """
    Read license plate from uploaded image using OCR.
    Supports JPEG, PNG images up to 10MB.
    Returns detected plate number with confidence score.
    """
    # Validate file size
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large (max 10MB)")
    
    # Call OCR
    result = await read_plate_from_image(contents)
    return result

@router.post("/ocr/full", response_model=LookupResponse)
async def ocr_and_lookup(file: UploadFile = File(...)):
    """
    Read license plate from image AND look up vehicle info.
    Combines OCR + vehicle lookup in one call.
    """
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large (max 10MB)")
    
    # OCR first
    ocr_result = await read_plate_from_image(contents)
    
    if not ocr_result.success or not ocr_result.plate:
        return LookupResponse(
            success=False,
            error=ocr_result.error or "No plate detected"
        )
    
    # Validate and lookup
    try:
        plaque = validate_plate(ocr_result.plate)
        vehicle = lookup_vehicle(plaque)
        return LookupResponse(
            success=True,
            vehicle=vehicle,
            source=f"ocr (confidence: {ocr_result.confidence})"
        )
    except ValueError:
        return LookupResponse(
            success=False,
            error=f"Invalid plate format: {ocr_result.plate}"
        )

@router.get("/ocr/health")
async def ocr_health():
    """Check if OCR service is configured"""
    return {
        "configured": bool(PLATE_RECOGNIZER_API_KEY),
        "provider": "Plate Recognizer" if PLATE_RECOGNIZER_API_KEY else None
    }
