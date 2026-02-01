"""OCR module - License plate recognition using Plate Recognizer API"""
import httpx
import base64
import os
from typing import Optional
from pydantic import BaseModel

PLATE_RECOGNIZER_API_KEY = os.getenv("PLATE_RECOGNIZER_API_KEY", "")
PLATE_RECOGNIZER_URL = "https://api.platerecognizer.com/v1/plate-reader/"

class PlateOCRResult(BaseModel):
    success: bool
    plate: Optional[str] = None
    confidence: Optional[float] = None
    region: Optional[str] = None
    vehicle_type: Optional[str] = None
    error: Optional[str] = None

async def read_plate_from_image(image_bytes: bytes) -> PlateOCRResult:
    """
    Read license plate from image using Plate Recognizer API
    
    Args:
        image_bytes: Raw image bytes (JPEG, PNG, etc.)
    
    Returns:
        PlateOCRResult with plate number and confidence
    """
    if not PLATE_RECOGNIZER_API_KEY:
        return PlateOCRResult(
            success=False,
            error="Plate Recognizer API key not configured"
        )
    
    try:
        # Encode image as base64
        image_b64 = base64.b64encode(image_bytes).decode()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                PLATE_RECOGNIZER_URL,
                headers={
                    "Authorization": f"Token {PLATE_RECOGNIZER_API_KEY}"
                },
                data={
                    "upload": image_b64,
                    "regions": "fr"  # Optimize for French plates
                }
            )
            
            if response.status_code == 403:
                return PlateOCRResult(
                    success=False,
                    error="Invalid API key or quota exceeded"
                )
            
            if response.status_code != 200 and response.status_code != 201:
                return PlateOCRResult(
                    success=False,
                    error=f"API error: {response.status_code}"
                )
            
            data = response.json()
            
            # Check if any plates were found
            results = data.get("results", [])
            if not results:
                return PlateOCRResult(
                    success=False,
                    error="No license plate detected in image"
                )
            
            # Get the first (best) result
            best = results[0]
            plate = best.get("plate", "").upper()
            score = best.get("score", 0)
            
            # Get region info
            region_info = best.get("region", {})
            region_code = region_info.get("code", "")
            
            # Get vehicle info if available
            vehicle = best.get("vehicle", {})
            vehicle_type = vehicle.get("type", "")
            
            return PlateOCRResult(
                success=True,
                plate=plate,
                confidence=round(score, 3),
                region=region_code,
                vehicle_type=vehicle_type
            )
            
    except httpx.RequestError as e:
        return PlateOCRResult(
            success=False,
            error=f"Network error: {str(e)}"
        )
    except Exception as e:
        return PlateOCRResult(
            success=False,
            error=f"OCR failed: {str(e)}"
        )
