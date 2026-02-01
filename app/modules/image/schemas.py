from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from enum import Enum


class BackgroundType(str, Enum):
    """Types d'arrière-plans disponibles."""
    TRANSPARENT = "transparent"
    SHOWROOM_INDOOR = "showroom_indoor"
    SHOWROOM_OUTDOOR = "showroom_outdoor"
    STUDIO_WHITE = "studio_white"
    STUDIO_GREY = "studio_grey"
    STUDIO_BLACK = "studio_black"
    GARAGE_MODERN = "garage_modern"
    GARAGE_LUXURY = "garage_luxury"
    PARKING_OUTDOOR = "parking_outdoor"
    CUSTOM = "custom"


class RemoveBackgroundRequest(BaseModel):
    """Request pour retirer l'arrière-plan."""
    image_url: str
    

class RemoveBackgroundResponse(BaseModel):
    """Response avec image sans fond."""
    id: str
    status: str
    original_url: str
    processed_url: str
    processing_time: float


class ApplyBackgroundRequest(BaseModel):
    """Request pour appliquer un arrière-plan pro."""
    image_url: str  # Image source (sera traitée pour remove-bg si besoin)
    transparent_url: Optional[str] = None  # Ou image déjà transparente
    background_type: BackgroundType = BackgroundType.SHOWROOM_INDOOR
    custom_background_url: Optional[str] = None  # Pour CUSTOM
    
    # Options de positionnement
    scale: float = 1.0  # 0.5 à 2.0
    position_x: float = 0.5  # 0.0 (gauche) à 1.0 (droite)
    position_y: float = 0.7  # 0.0 (haut) à 1.0 (bas), 0.7 = vers le bas
    add_shadow: bool = True
    add_reflection: bool = False


class ApplyBackgroundResponse(BaseModel):
    """Response avec image finale."""
    id: str
    status: str
    original_url: str
    background_type: str
    processed_url: str
    processing_time: float


class BackgroundInfo(BaseModel):
    """Info sur un arrière-plan disponible."""
    id: str
    name: str
    category: str
    preview_url: str
    description: Optional[str] = None


class BackgroundListResponse(BaseModel):
    """Liste des arrière-plans disponibles."""
    backgrounds: List[BackgroundInfo]
    total: int
