"""
API endpoints pour le traitement d'images Keroxio.

Endpoints:
- POST /remove-bg : Supprime l'arrière-plan
- POST /remove-bg/upload : Supprime l'arrière-plan (upload)
- POST /apply-background : Applique un fond pro
- POST /process : Pipeline complet (remove-bg + background)
- GET /backgrounds : Liste les fonds disponibles
- POST /info : Métadonnées image
- POST /resize : Redimensionner
- GET /health : Status du service
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import base64
import uuid
import io

from .schemas import (
    RemoveBackgroundRequest,
    RemoveBackgroundResponse,
    ApplyBackgroundRequest,
    ApplyBackgroundResponse,
    BackgroundType,
    BackgroundListResponse,
    BackgroundInfo,
)
from .service import get_image_service
from .backgrounds import list_backgrounds, BACKGROUNDS

router = APIRouter(prefix="/image", tags=["Image Processing"])


@router.get("/health")
async def health():
    """Status du module image."""
    from app.core.config import settings
    from .service import AUTOBG_BACKGROUNDS
    
    autobg_configured = bool(getattr(settings, 'AUTOBG_API_KEY', None))
    
    pillow_ok = False
    try:
        from PIL import Image
        pillow_ok = True
    except ImportError:
        pass
    
    return {
        "status": "healthy",
        "module": "image",
        "autobg_configured": autobg_configured,
        "pillow_available": pillow_ok,
        "backgrounds_available": len(BACKGROUNDS),
        "autobg_backgrounds": len(AUTOBG_BACKGROUNDS),
    }


@router.get("/autobg-backgrounds")
async def list_autobg_backgrounds():
    """Liste les backgrounds supportés par AutoBG.ai."""
    service = get_image_service()
    return await service.list_autobg_backgrounds()


@router.get("/backgrounds", response_model=BackgroundListResponse)
async def get_backgrounds():
    """Liste tous les arrière-plans professionnels disponibles."""
    backgrounds = list_backgrounds()
    return BackgroundListResponse(
        backgrounds=[
            BackgroundInfo(
                id=bg["id"],
                name=bg["name"],
                category=bg["category"],
                preview_url=bg.get("preview_url", ""),
                description=bg.get("description"),
            )
            for bg in backgrounds
        ],
        total=len(backgrounds),
    )


@router.get("/backgrounds/{category}")
async def get_backgrounds_by_category(category: str):
    """Liste les arrière-plans d'une catégorie (showroom, studio, garage, outdoor)."""
    backgrounds = [
        bg for bg in list_backgrounds() 
        if bg["category"] == category
    ]
    return {
        "category": category,
        "backgrounds": backgrounds,
        "total": len(backgrounds),
    }


@router.post("/remove-bg", response_model=RemoveBackgroundResponse)
async def remove_background(request: RemoveBackgroundRequest):
    """
    Supprime l'arrière-plan d'une image.
    
    Utilise AutoBG.ai pour un résultat optimisé véhicules.
    Retourne une image PNG avec fond transparent.
    """
    service = get_image_service()
    
    try:
        result = await service.remove_background(request.image_url)
        return RemoveBackgroundResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-bg/upload", response_model=RemoveBackgroundResponse)
async def remove_background_upload(file: UploadFile = File(...)):
    """
    Supprime l'arrière-plan d'une image uploadée.
    
    Accepte: JPEG, PNG, WebP
    Retourne: URL de l'image transparente
    """
    from app.core.config import settings
    from pathlib import Path
    
    # Valider le type de fichier
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(400, "Format non supporté. Utilisez JPEG, PNG ou WebP.")
    
    # Sauvegarder temporairement
    content = await file.read()
    
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="Image trop grande (max 10MB)")
    
    filename = f"upload_{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    
    storage_path = Path(getattr(settings, 'STORAGE_PATH', '/tmp/storage'))
    uploads_path = storage_path / "uploads"
    uploads_path.mkdir(parents=True, exist_ok=True)
    
    file_path = uploads_path / filename
    file_path.write_bytes(content)
    
    storage_url = getattr(settings, 'STORAGE_URL', 'https://storage.keroxio.fr')
    image_url = f"{storage_url}/uploads/{filename}"
    
    # Traiter
    service = get_image_service()
    try:
        result = await service.remove_background(image_url)
        return RemoveBackgroundResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-background", response_model=ApplyBackgroundResponse)
async def apply_background(request: ApplyBackgroundRequest):
    """
    Applique un arrière-plan professionnel à une image.
    
    Si image_url n'a pas de fond transparent, il sera d'abord supprimé.
    
    Options:
    - background_type: Type de fond (showroom_indoor, studio_white, etc.)
    - scale: Échelle de la voiture (0.5 à 2.0)
    - position_x/y: Position (0.0 à 1.0)
    - add_shadow: Ajouter une ombre réaliste
    - add_reflection: Ajouter un reflet (style showroom luxe)
    """
    service = get_image_service()
    
    try:
        # Utiliser l'image transparente fournie ou traiter l'image source
        if request.transparent_url:
            transparent_url = request.transparent_url
        else:
            # Remove background first
            result_bg = await service.remove_background(request.image_url)
            transparent_url = result_bg["processed_url"]
        
        result = await service.apply_background(
            transparent_url=transparent_url,
            background_type=request.background_type.value,
            custom_background_url=request.custom_background_url,
            scale=request.scale,
            position_x=request.position_x,
            position_y=request.position_y,
            add_shadow=request.add_shadow,
            add_reflection=request.add_reflection,
        )
        
        return ApplyBackgroundResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process", response_model=ApplyBackgroundResponse)
async def process_complete(
    image_url: str = Form(...),
    background_type: BackgroundType = Form(BackgroundType.SHOWROOM_INDOOR),
    scale: float = Form(1.0),
    position_x: float = Form(0.5),
    position_y: float = Form(0.7),
    add_shadow: bool = Form(True),
    add_reflection: bool = Form(False),
):
    """
    Pipeline complet: Remove background + Apply background.
    
    Une seule requête pour obtenir le résultat final.
    """
    service = get_image_service()
    
    try:
        result = await service.process_complete(
            image_url=image_url,
            background_type=background_type.value,
            scale=scale,
            position_x=position_x,
            position_y=position_y,
            add_shadow=add_shadow,
            add_reflection=add_reflection,
        )
        return ApplyBackgroundResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/upload", response_model=ApplyBackgroundResponse)
async def process_complete_upload(
    file: UploadFile = File(...),
    background_type: BackgroundType = Form(BackgroundType.SHOWROOM_INDOOR),
    scale: float = Form(1.0),
    position_x: float = Form(0.5),
    position_y: float = Form(0.7),
    add_shadow: bool = Form(True),
    add_reflection: bool = Form(False),
):
    """
    Pipeline complet avec upload direct.
    
    Upload une image, supprime le fond, applique le background choisi.
    """
    from app.core.config import settings
    from pathlib import Path
    
    # Valider le type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(400, "Format non supporté. Utilisez JPEG, PNG ou WebP.")
    
    # Sauvegarder
    content = await file.read()
    
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image trop grande (max 10MB)")
    
    filename = f"upload_{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    
    storage_path = Path(getattr(settings, 'STORAGE_PATH', '/tmp/storage'))
    uploads_path = storage_path / "uploads"
    uploads_path.mkdir(parents=True, exist_ok=True)
    
    file_path = uploads_path / filename
    file_path.write_bytes(content)
    
    storage_url = getattr(settings, 'STORAGE_URL', 'https://storage.keroxio.fr')
    image_url = f"{storage_url}/uploads/{filename}"
    
    # Traiter
    service = get_image_service()
    try:
        result = await service.process_complete(
            image_url=image_url,
            background_type=background_type.value,
            scale=scale,
            position_x=position_x,
            position_y=position_y,
            add_shadow=add_shadow,
            add_reflection=add_reflection,
        )
        return ApplyBackgroundResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Utilitaires ===

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
            "has_alpha": img.mode in ("RGBA", "LA", "PA"),
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Pillow non installé")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image invalide: {str(e)}")


@router.post("/resize")
async def resize_image(
    file: UploadFile = File(...),
    width: int = Query(..., ge=1, le=4096),
    height: int = Query(..., ge=1, le=4096),
    maintain_aspect: bool = Query(True),
):
    """Redimensionne une image."""
    try:
        from PIL import Image
        
        image_bytes = await file.read()
        img = Image.open(io.BytesIO(image_bytes))
        
        if maintain_aspect:
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        
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
        raise HTTPException(status_code=503, detail="Pillow non installé")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur: {str(e)}")
