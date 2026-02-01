"""
Vehicle models - Stockage des véhicules traités par Keroxio
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

from app.core.database import Base


class Vehicle(Base):
    """Véhicule créé par un utilisateur dans le flow Keroxio."""
    __tablename__ = "vehicles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Identification
    plaque = Column(String(15), nullable=False, index=True)
    
    # Infos véhicule (from SIV/OCR)
    marque = Column(String(50), nullable=True)
    modele = Column(String(100), nullable=True)
    version = Column(String(100), nullable=True)
    annee = Column(Integer, nullable=True)
    carburant = Column(String(20), nullable=True)  # essence, diesel, electrique, hybride
    boite = Column(String(20), nullable=True)  # manuelle, automatique
    kilometrage = Column(Integer, nullable=True)
    couleur = Column(String(50), nullable=True)
    puissance = Column(String(20), nullable=True)
    
    # Prix
    prix_estime_min = Column(Integer, nullable=True)
    prix_estime_moyen = Column(Integer, nullable=True)
    prix_estime_max = Column(Integer, nullable=True)
    prix_choisi = Column(Integer, nullable=True)
    
    # Photos (URLs des images traitées)
    photos_originales = Column(JSON, default=list)  # List of original photo URLs
    photos_traitees = Column(JSON, default=list)    # List of processed photo URLs
    background_utilise = Column(String(50), nullable=True)
    
    # Annonce
    annonce_titre = Column(String(200), nullable=True)
    annonce_description = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default="draft")  # draft, ready, published
    published_platforms = Column(JSON, default=list)  # ["leboncoin", "lacentrale"]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
