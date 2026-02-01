"""
API endpoints pour le traitement d'images Keroxio.
Option B: Remove-bg local + Composite Pillow.

Endpoints:
- POST /remove-bg : Supprime l'arrière-plan → PNG transparent
- POST /composite : Fusionne voiture + background
- POST /process : Pipeline complet (remove-bg + composite)
- GET /backgrounds : Liste les backgrounds disponibles
- POST /backgrounds : Ajoute un nouveau background
- GET /health : Status du service
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import io

from .service import get_image_service

router = APIRouter(prefix="/image", tags=["Image Processing"])


# ========== SCHEMAS ==========

class RemoveBgRequest(BaseModel):
    image_url: str


class RemoveBgResponse(BaseModel):
    id: str
    status: str
    transparent_url: str
    processing_time: float


class CompositeRequest(BaseModel):
    car_url: str  # PNG transparent
    background: str
    position: str = "center"
    scale: float = 0.85
    vertical_offset: float = 0.0  # -0.1 to 0.1 (negative = lower)


class ProcessRequest(BaseModel):
    image_url: str
    background: str
    position: str = "center"
    scale: float = 0.85
    vertical_offset: float = 0.0  # -0.1 to 0.1 (negative = lower)


class ProcessResponse(BaseModel):
    id: str
    status: str
    transparent_url: str
    final_url: str
    background: str
    processing_time: float


class BackgroundInfo(BaseModel):
    name: str
    filename: str
    url: Optional[str] = None


# ========== ENDPOINTS ==========

@router.get("/health")
async def health():
    """Status du module image."""
    service = get_image_service()
    
    # Check if rembg is available
    rembg_available = False
    try:
        import rembg
        rembg_available = True
    except ImportError:
        pass
    
    # Check if remove.bg API key is configured
    from app.core.config import settings
    removebg_configured = bool(getattr(settings, 'REMOVEBG_API_KEY', None))
    
    backgrounds = service.list_backgrounds()
    
    return {
        "status": "healthy",
        "module": "image",
        "rembg_available": rembg_available,
        "removebg_configured": removebg_configured,
        "backgrounds_count": len(backgrounds),
    }


@router.get("/backgrounds")
async def list_backgrounds():
    """Liste les backgrounds disponibles."""
    service = get_image_service()
    backgrounds = service.list_backgrounds()
    
    return {
        "backgrounds": backgrounds,
        "count": len(backgrounds),
    }


@router.post("/backgrounds")
async def add_background(
    file: UploadFile = File(...),
    name: str = Form(...),
):
    """Ajoute un nouveau background."""
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(400, "Format non supporté. Utilisez JPEG, PNG ou WebP.")
    
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, "Image trop grande (max 20MB)")
    
    service = get_image_service()
    try:
        result = await service.add_background(name, content)
        return result
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/remove-bg")
async def remove_background(request: RemoveBgRequest):
    """
    Supprime l'arrière-plan d'une image.
    
    Retourne un PNG avec fond transparent.
    """
    service = get_image_service()
    
    try:
        # Download image
        image_bytes = await service.download_image(request.image_url)
        
        # Remove background
        import time
        import uuid
        start = time.time()
        request_id = str(uuid.uuid4())
        
        transparent = await service.remove_background(image_bytes)
        
        # Save result
        from pathlib import Path
        filename = f"{request_id}_transparent.png"
        filepath = service.storage_path / "processed" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(transparent)
        
        return {
            "id": request_id,
            "status": "completed",
            "transparent_url": f"{service.api_url}/image/files/{filename}",
            "processing_time": round(time.time() - start, 2),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/remove-bg/upload")
async def remove_background_upload(
    file: UploadFile = File(...),
):
    """
    Supprime l'arrière-plan d'une image uploadée.
    Retourne directement le PNG transparent.
    """
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(400, "Format non supporté. Utilisez JPEG, PNG ou WebP.")
    
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image trop grande (max 10MB)")
    
    service = get_image_service()
    try:
        transparent = await service.remove_background(content)
        
        return Response(
            content=transparent,
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=transparent.png"}
        )
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/composite")
async def composite(request: CompositeRequest):
    """
    Fusionne une voiture (PNG transparent) avec un background.
    
    Args:
        car_url: URL du PNG transparent de la voiture
        background: Nom du background (showroom, garage, etc.)
        position: center, left, right
        scale: 0.5 à 1.0
    """
    service = get_image_service()
    
    try:
        # Download car PNG
        car_bytes = await service.download_image(request.car_url)
        
        # Composite
        import time
        import uuid
        start = time.time()
        request_id = str(uuid.uuid4())
        
        result = await service.composite(
            car_bytes,
            request.background,
            position=request.position,
            scale=request.scale,
        )
        
        # Save result
        filename = f"{request_id}_final.jpg"
        filepath = service.storage_path / "processed" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(result)
        
        return {
            "id": request_id,
            "status": "completed",
            "final_url": f"{service.api_url}/image/files/{filename}",
            "background": request.background,
            "processing_time": round(time.time() - start, 2),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/process", response_model=ProcessResponse)
async def process_image(request: ProcessRequest):
    """
    Pipeline complet: remove-bg + composite.
    
    1. Télécharge l'image
    2. Supprime l'arrière-plan
    3. Fusionne avec le background choisi
    
    Args:
        image_url: URL de l'image de la voiture
        background: Nom du background
        position: center, left, right
        scale: 0.5 à 1.0
    """
    service = get_image_service()
    
    try:
        # Download image
        image_bytes = await service.download_image(request.image_url)
        
        # Full pipeline
        result = await service.process_image(
            image_bytes,
            request.background,
            position=request.position,
            scale=request.scale,
            vertical_offset=request.vertical_offset,
        )
        
        return ProcessResponse(**result)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/process/upload", response_model=ProcessResponse)
async def process_image_upload(
    file: UploadFile = File(...),
    background: str = Form(...),
    position: str = Form("center"),
    scale: float = Form(0.85),
    vertical_offset: float = Form(0.0),
):
    """
    Pipeline complet avec upload direct.
    
    vertical_offset: -0.1 à 0.1 (négatif = plus bas sur l'image)
    """
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(400, "Format non supporté. Utilisez JPEG, PNG ou WebP.")
    
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image trop grande (max 10MB)")
    
    service = get_image_service()
    try:
        result = await service.process_image(
            content,
            background,
            position=position,
            scale=scale,
            vertical_offset=vertical_offset,
        )
        return ProcessResponse(**result)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/info")
async def get_info(file: UploadFile = File(...)):
    """Récupère les métadonnées d'une image."""
    try:
        image_bytes = await file.read()
        service = get_image_service()
        return service.get_image_info(image_bytes)
    except Exception as e:
        raise HTTPException(400, f"Image invalide: {str(e)}")


@router.get("/files/{filename}")
async def get_processed_file(filename: str):
    """Récupère un fichier traité."""
    service = get_image_service()
    filepath = service.storage_path / "processed" / filename
    
    if not filepath.exists():
        raise HTTPException(404, "File not found")
    
    # Determine media type
    media_type = "image/png" if filename.endswith(".png") else "image/jpeg"
    
    return FileResponse(
        path=filepath,
        media_type=media_type,
        filename=filename,
    )


@router.get("/backgrounds/{filename}")
async def get_background_file(filename: str):
    """Récupère un fichier background."""
    service = get_image_service()
    
    # Check storage/backgrounds first
    filepath = service.storage_path / "backgrounds" / filename
    if not filepath.exists():
        # Check backgrounds_images folder
        filepath = service.backgrounds_path / filename
    
    if not filepath.exists():
        raise HTTPException(404, "Background not found")
    
    media_type = "image/png" if filename.endswith(".png") else "image/jpeg"
    
    return FileResponse(
        path=filepath,
        media_type=media_type,
        filename=filename,
    )
