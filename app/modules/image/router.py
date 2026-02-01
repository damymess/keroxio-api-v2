"""Image router - Background removal and image processing"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io
import base64
import httpx

router = APIRouter()

# Config - utilise le service rembg externe ou local
REMBG_ENABLED = True

# === Schemas ===
class RemoveBgRequest(BaseModel):
    image_base64: str
    output_format: str = "png"

class RemoveBgResponse(BaseModel):
    success: bool
    image_base64: Optional[str] = None
    format: str = "png"
    error: Optional[str] = None

class ImageInfoResponse(BaseModel):
    width: int
    height: int
    format: str
    size_bytes: int
    has_alpha: bool

# === Helpers ===
async def remove_background_rembg(image_bytes: bytes) -> bytes:
    """Remove background using rembg library"""
    try:
        from rembg import remove
        output = remove(image_bytes)
        return output
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="rembg not installed. Run: pip install rembg[gpu]"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Background removal failed: {str(e)}")

def get_image_info(image_bytes: bytes) -> dict:
    """Get image metadata using PIL"""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format or "unknown",
            "size_bytes": len(image_bytes),
            "has_alpha": img.mode in ("RGBA", "LA", "PA")
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Pillow not installed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

# === Endpoints ===
@router.post("/remove-bg", response_model=RemoveBgResponse)
async def remove_background_base64(request: RemoveBgRequest):
    """Remove background from base64 encoded image"""
    try:
        # Decode base64
        if "," in request.image_base64:
            # Handle data URL format
            image_bytes = base64.b64decode(request.image_base64.split(",")[1])
        else:
            image_bytes = base64.b64decode(request.image_base64)
        
        # Remove background
        result_bytes = await remove_background_rembg(image_bytes)
        
        # Encode result
        result_base64 = base64.b64encode(result_bytes).decode()
        
        return RemoveBgResponse(
            success=True,
            image_base64=result_base64,
            format=request.output_format
        )
    except HTTPException:
        raise
    except Exception as e:
        return RemoveBgResponse(
            success=False,
            error=str(e)
        )

@router.post("/remove-bg/upload")
async def remove_background_upload(
    file: UploadFile = File(...),
    output_format: str = Query("png", regex="^(png|webp)$")
):
    """Remove background from uploaded image file"""
    # Read file
    image_bytes = await file.read()
    
    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="Image too large (max 10MB)")
    
    # Remove background
    result_bytes = await remove_background_rembg(image_bytes)
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(result_bytes),
        media_type=f"image/{output_format}",
        headers={
            "Content-Disposition": f"attachment; filename=result.{output_format}"
        }
    )

@router.post("/info", response_model=ImageInfoResponse)
async def get_info(file: UploadFile = File(...)):
    """Get image metadata"""
    image_bytes = await file.read()
    info = get_image_info(image_bytes)
    return ImageInfoResponse(**info)

@router.post("/resize")
async def resize_image(
    file: UploadFile = File(...),
    width: int = Query(..., ge=1, le=4096),
    height: int = Query(..., ge=1, le=4096),
    maintain_aspect: bool = Query(True)
):
    """Resize an image"""
    try:
        from PIL import Image
        
        image_bytes = await file.read()
        img = Image.open(io.BytesIO(image_bytes))
        
        if maintain_aspect:
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        fmt = img.format or "PNG"
        img.save(output, format=fmt)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type=f"image/{fmt.lower()}",
            headers={"Content-Disposition": f"attachment; filename=resized.{fmt.lower()}"}
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="Pillow not installed")

@router.get("/health")
async def health():
    """Check if image processing is available"""
    status = {"rembg": False, "pillow": False}
    
    try:
        import rembg
        status["rembg"] = True
    except ImportError:
        pass
    
    try:
        from PIL import Image
        status["pillow"] = True
    except ImportError:
        pass
    
    return {
        "available": status["rembg"] and status["pillow"],
        "dependencies": status
    }
