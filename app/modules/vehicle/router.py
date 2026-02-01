"""
Vehicle API - CRUD pour les véhicules Keroxio
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from .models import Vehicle

router = APIRouter(prefix="/vehicle", tags=["Vehicle"])


# ========== SCHEMAS ==========

class VehicleCreate(BaseModel):
    plaque: str
    marque: Optional[str] = None
    modele: Optional[str] = None
    version: Optional[str] = None
    annee: Optional[int] = None
    carburant: Optional[str] = None
    boite: Optional[str] = None
    kilometrage: Optional[int] = None
    couleur: Optional[str] = None
    puissance: Optional[str] = None


class VehicleUpdate(BaseModel):
    marque: Optional[str] = None
    modele: Optional[str] = None
    version: Optional[str] = None
    annee: Optional[int] = None
    carburant: Optional[str] = None
    boite: Optional[str] = None
    kilometrage: Optional[int] = None
    couleur: Optional[str] = None
    puissance: Optional[str] = None
    prix_estime_min: Optional[int] = None
    prix_estime_moyen: Optional[int] = None
    prix_estime_max: Optional[int] = None
    prix_choisi: Optional[int] = None
    photos_originales: Optional[List[str]] = None
    photos_traitees: Optional[List[str]] = None
    background_utilise: Optional[str] = None
    annonce_titre: Optional[str] = None
    annonce_description: Optional[str] = None
    status: Optional[str] = None


class VehicleResponse(BaseModel):
    id: str
    plaque: str
    marque: Optional[str]
    modele: Optional[str]
    version: Optional[str]
    annee: Optional[int]
    carburant: Optional[str]
    boite: Optional[str]
    kilometrage: Optional[int]
    couleur: Optional[str]
    puissance: Optional[str]
    prix_estime_min: Optional[int]
    prix_estime_moyen: Optional[int]
    prix_estime_max: Optional[int]
    prix_choisi: Optional[int]
    photos_originales: List[str]
    photos_traitees: List[str]
    background_utilise: Optional[str]
    annonce_titre: Optional[str]
    annonce_description: Optional[str]
    status: str
    published_platforms: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ========== ENDPOINTS ==========

@router.post("/", response_model=VehicleResponse)
async def create_vehicle(
    data: VehicleCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Créer un nouveau véhicule."""
    vehicle = Vehicle(
        user_id=current_user["id"],
        plaque=data.plaque.upper(),
        marque=data.marque,
        modele=data.modele,
        version=data.version,
        annee=data.annee,
        carburant=data.carburant,
        boite=data.boite,
        kilometrage=data.kilometrage,
        couleur=data.couleur,
        puissance=data.puissance,
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    
    return _vehicle_to_response(vehicle)


@router.get("/", response_model=List[VehicleResponse])
async def list_vehicles(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liste les véhicules de l'utilisateur."""
    query = select(Vehicle).where(Vehicle.user_id == current_user["id"])
    
    if status:
        query = query.where(Vehicle.status == status)
    
    query = query.order_by(desc(Vehicle.created_at)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    vehicles = result.scalars().all()
    
    return [_vehicle_to_response(v) for v in vehicles]


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Récupère un véhicule par ID."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.user_id == current_user["id"]
        )
    )
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return _vehicle_to_response(vehicle)


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    data: VehicleUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Met à jour un véhicule."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.user_id == current_user["id"]
        )
    )
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)
    
    await db.commit()
    await db.refresh(vehicle)
    
    return _vehicle_to_response(vehicle)


@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supprime un véhicule."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.user_id == current_user["id"]
        )
    )
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    await db.delete(vehicle)
    await db.commit()
    
    return {"message": "Vehicle deleted"}


@router.post("/{vehicle_id}/publish")
async def mark_published(
    vehicle_id: str,
    platform: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marque le véhicule comme publié sur une plateforme."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.user_id == current_user["id"]
        )
    )
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    platforms = vehicle.published_platforms or []
    if platform not in platforms:
        platforms.append(platform)
    
    vehicle.published_platforms = platforms
    vehicle.status = "published"
    
    await db.commit()
    
    return {"message": f"Marked as published on {platform}"}


# ========== HELPERS ==========

def _vehicle_to_response(vehicle: Vehicle) -> VehicleResponse:
    return VehicleResponse(
        id=str(vehicle.id),
        plaque=vehicle.plaque,
        marque=vehicle.marque,
        modele=vehicle.modele,
        version=vehicle.version,
        annee=vehicle.annee,
        carburant=vehicle.carburant,
        boite=vehicle.boite,
        kilometrage=vehicle.kilometrage,
        couleur=vehicle.couleur,
        puissance=vehicle.puissance,
        prix_estime_min=vehicle.prix_estime_min,
        prix_estime_moyen=vehicle.prix_estime_moyen,
        prix_estime_max=vehicle.prix_estime_max,
        prix_choisi=vehicle.prix_choisi,
        photos_originales=vehicle.photos_originales or [],
        photos_traitees=vehicle.photos_traitees or [],
        background_utilise=vehicle.background_utilise,
        annonce_titre=vehicle.annonce_titre,
        annonce_description=vehicle.annonce_description,
        status=vehicle.status,
        published_platforms=vehicle.published_platforms or [],
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )
