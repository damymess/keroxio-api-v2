"""
API endpoints pour le traitement d'images Keroxio.
Intégration AutoBG.ai

Endpoints:
- POST /remove-bg : Supprime l'arrière-plan (sans template)
- POST /process : Traite avec un template (background)
- GET /templates : Liste les templates AutoBG
- POST /templates : Crée un nouveau template
- GET /credits : Crédits restants
- GET /health : Status du service
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import io

from .service import get_image_service

router = APIRouter(prefix="/image", tags=["Image Processing"])


# ========== SCHEMAS ==========

class RemoveBgRequest(BaseModel):
    image_url: str
    hide_plate: bool = False


class RemoveBgResponse(BaseModel):
    id: str
    status: str
    original_url: str
    processed_url: str
    processing_time: float


class ProcessRequest(BaseModel):
    image_url: str
    template_name: str
    background_url: str
    hide_plate: bool = False


class ProcessResponse(BaseModel):
    id: str
    status: str
    original_url: str
    processed_url: str
    template_name: str
    template_id: int
    processing_time: float


class TemplateInfo(BaseModel):
    id: int
    name: str


# ========== ENDPOINTS ==========

@router.get("/health")
async def health():
    """Status du module image."""
    from app.core.config import settings
    
    autobg_configured = bool(getattr(settings, 'AUTOBG_API_KEY', None))
    
    return {
        "status": "healthy",
        "module": "image",
        "autobg_configured": autobg_configured,
        "api_base": "https://apis.autobg.ai/public/api/v1",
    }


@router.get("/credits")
async def get_credits():
    """Récupère les crédits AutoBG restants."""
    service = get_image_service()
    try:
        return await service.get_credits()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_templates():
    """Liste les templates AutoBG disponibles."""
    service = get_image_service()
    try:
        templates = await service.list_templates()
        return {
            "templates": templates,
            "count": len(templates),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-bg", response_model=RemoveBgResponse)
async def remove_background(request: RemoveBgRequest):
    """
    Supprime l'arrière-plan d'une image via AutoBG.ai.
    
    Utilise le mode "sans template" - retourne une image avec fond transparent.
    
    Options:
    - hide_plate: Masquer la plaque d'immatriculation
    """
    service = get_image_service()
    
    try:
        result = await service.remove_background(
            image_url=request.image_url,
            hide_plate=request.hide_plate,
        )
        return RemoveBgResponse(
            id=result["id"],
            status=result["status"],
            original_url=result["original_url"],
            processed_url=result["processed_url"],
            processing_time=result["processing_time"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-bg/upload", response_model=RemoveBgResponse)
async def remove_background_upload(
    file: UploadFile = File(...),
    hide_plate: bool = Form(False),
):
    """
    Supprime l'arrière-plan d'une image uploadée.
    """
    from app.core.config import settings
    from pathlib import Path
    
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(400, "Format non supporté. Utilisez JPEG, PNG ou WebP.")
    
    # Save uploaded file
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image trop grande (max 10MB)")
    
    filename = f"upload_{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    storage_path = Path(getattr(settings, 'STORAGE_PATH', '/tmp/storage'))
    uploads_path = storage_path / "uploads"
    uploads_path.mkdir(parents=True, exist_ok=True)
    
    file_path = uploads_path / filename
    file_path.write_bytes(content)
    
    storage_url = getattr(settings, 'STORAGE_URL', 'https://storage.keroxio.fr')
    image_url = f"{storage_url}/uploads/{filename}"
    
    # Process
    service = get_image_service()
    try:
        result = await service.remove_background(
            image_url=image_url,
            hide_plate=hide_plate,
        )
        return RemoveBgResponse(
            id=result["id"],
            status=result["status"],
            original_url=result["original_url"],
            processed_url=result["processed_url"],
            processing_time=result["processing_time"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process", response_model=ProcessResponse)
async def process_with_template(request: ProcessRequest):
    """
    Traite une image avec un template AutoBG (background custom).
    
    Le template sera créé automatiquement s'il n'existe pas.
    
    Args:
    - image_url: URL de l'image de la voiture
    - template_name: Nom unique du template
    - background_url: URL de l'image de fond
    - hide_plate: Masquer la plaque
    """
    service = get_image_service()
    
    try:
        result = await service.process_with_template(
            image_url=request.image_url,
            template_name=request.template_name,
            background_url=request.background_url,
            hide_plate=request.hide_plate,
        )
        return ProcessResponse(
            id=result["id"],
            status=result["status"],
            original_url=result["original_url"],
            processed_url=result["processed_url"],
            template_name=result["template_name"],
            template_id=result["template_id"],
            processing_time=result["processing_time"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/upload", response_model=ProcessResponse)
async def process_upload_with_template(
    file: UploadFile = File(...),
    template_name: str = Form(...),
    background_url: str = Form(...),
    hide_plate: bool = Form(False),
):
    """
    Traite une image uploadée avec un template.
    """
    from app.core.config import settings
    from pathlib import Path
    
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(400, "Format non supporté. Utilisez JPEG, PNG ou WebP.")
    
    # Save uploaded file
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image trop grande (max 10MB)")
    
    filename = f"upload_{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    storage_path = Path(getattr(settings, 'STORAGE_PATH', '/tmp/storage'))
    uploads_path = storage_path / "uploads"
    uploads_path.mkdir(parents=True, exist_ok=True)
    
    file_path = uploads_path / filename
    file_path.write_bytes(content)
    
    storage_url = getattr(settings, 'STORAGE_URL', 'https://storage.keroxio.fr')
    image_url = f"{storage_url}/uploads/{filename}"
    
    # Process
    service = get_image_service()
    try:
        result = await service.process_with_template(
            image_url=image_url,
            template_name=template_name,
            background_url=background_url,
            hide_plate=hide_plate,
        )
        return ProcessResponse(
            id=result["id"],
            status=result["status"],
            original_url=result["original_url"],
            processed_url=result["processed_url"],
            template_name=result["template_name"],
            template_id=result["template_id"],
            processing_time=result["processing_time"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== UTILITIES ==========

@router.post("/info")
async def get_info(file: UploadFile = File(...)):
    """Récupère les métadonnées d'une image."""
    try:
        from PIL import Image
        
        image_bytes = await file.read()
        img = Image.open(io.BytesIO(image_bytes))
        
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format or "unknown",
            "mode": img.mode,
            "size_bytes": len(image_bytes),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image invalide: {str(e)}")
