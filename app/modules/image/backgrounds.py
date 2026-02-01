"""
Collection d'arrière-plans professionnels pour photos de véhicules.

Ces images sont stockées sur storage.keroxio.fr ou générées dynamiquement.
Pour ajouter un nouveau fond: ajouter l'entrée ici + uploader l'image.
"""

from typing import Dict, Any

# Configuration des arrière-plans disponibles
BACKGROUNDS: Dict[str, Dict[str, Any]] = {
    # Showrooms
    "showroom_indoor": {
        "name": "Showroom Intérieur",
        "category": "showroom",
        "description": "Concession automobile moderne avec éclairage studio",
        "url": "https://storage.keroxio.fr/backgrounds/showroom-indoor.jpg",
        "preview_url": "https://storage.keroxio.fr/backgrounds/thumbs/showroom-indoor.jpg",
        "settings": {
            "default_y": 0.75,  # Voiture positionnée vers le bas
            "floor_level": 0.85,  # Pour le reflet
            "ambient_color": "#f5f5f5",
        }
    },
    "showroom_outdoor": {
        "name": "Showroom Extérieur",
        "category": "showroom", 
        "description": "Espace extérieur premium avec végétation",
        "url": "https://storage.keroxio.fr/backgrounds/showroom-outdoor.jpg",
        "preview_url": "https://storage.keroxio.fr/backgrounds/thumbs/showroom-outdoor.jpg",
        "settings": {
            "default_y": 0.7,
            "floor_level": 0.8,
            "ambient_color": "#e8f0e8",
        }
    },
    
    # Studios
    "studio_white": {
        "name": "Studio Blanc",
        "category": "studio",
        "description": "Fond blanc professionnel style catalogue",
        "color": "#FFFFFF",
        "gradient": ["#FFFFFF", "#F0F0F0"],
        "preview_url": "https://storage.keroxio.fr/backgrounds/thumbs/studio-white.jpg",
        "settings": {
            "default_y": 0.7,
            "floor_level": 0.85,
            "add_shadow": True,
        }
    },
    "studio_grey": {
        "name": "Studio Gris",
        "category": "studio",
        "description": "Fond gris neutre professionnel",
        "color": "#808080",
        "gradient": ["#909090", "#606060"],
        "preview_url": "https://storage.keroxio.fr/backgrounds/thumbs/studio-grey.jpg",
        "settings": {
            "default_y": 0.7,
            "floor_level": 0.85,
            "add_shadow": True,
        }
    },
    "studio_black": {
        "name": "Studio Noir",
        "category": "studio",
        "description": "Fond noir premium style sport/luxe",
        "color": "#1A1A1A",
        "gradient": ["#2A2A2A", "#0A0A0A"],
        "preview_url": "https://storage.keroxio.fr/backgrounds/thumbs/studio-black.jpg",
        "settings": {
            "default_y": 0.7,
            "floor_level": 0.85,
            "add_shadow": True,
            "shadow_opacity": 0.3,
        }
    },
    
    # Garages modernes
    "garage_modern": {
        "name": "Garage Moderne",
        "category": "garage",
        "description": "Atelier moderne avec sol époxy et éclairage LED",
        "url": "https://storage.keroxio.fr/backgrounds/garage-modern.jpg",
        "preview_url": "https://storage.keroxio.fr/backgrounds/thumbs/garage-modern.jpg",
        "settings": {
            "default_y": 0.72,
            "floor_level": 0.82,
            "ambient_color": "#e0e5e8",
        }
    },
    "garage_luxury": {
        "name": "Garage Luxe",
        "category": "garage",
        "description": "Garage haut de gamme style collection privée",
        "url": "https://storage.keroxio.fr/backgrounds/garage-luxury.jpg",
        "preview_url": "https://storage.keroxio.fr/backgrounds/thumbs/garage-luxury.jpg",
        "settings": {
            "default_y": 0.7,
            "floor_level": 0.8,
            "ambient_color": "#d4c8b8",
        }
    },
    
    # Extérieur
    "parking_outdoor": {
        "name": "Parking Extérieur",
        "category": "outdoor",
        "description": "Parking avec vue urbaine moderne",
        "url": "https://storage.keroxio.fr/backgrounds/parking-outdoor.jpg",
        "preview_url": "https://storage.keroxio.fr/backgrounds/thumbs/parking-outdoor.jpg",
        "settings": {
            "default_y": 0.75,
            "floor_level": 0.85,
            "ambient_color": "#c8d0d8",
        }
    },
}


def get_background(bg_type: str) -> Dict[str, Any]:
    """Récupère la config d'un arrière-plan."""
    return BACKGROUNDS.get(bg_type)


def list_backgrounds() -> list:
    """Liste tous les arrière-plans disponibles."""
    result = []
    for bg_id, bg_data in BACKGROUNDS.items():
        result.append({
            "id": bg_id,
            "name": bg_data["name"],
            "category": bg_data["category"],
            "description": bg_data.get("description", ""),
            "preview_url": bg_data.get("preview_url", ""),
        })
    return result


def get_backgrounds_by_category(category: str) -> list:
    """Filtre les arrière-plans par catégorie."""
    return [
        {"id": bg_id, **bg_data}
        for bg_id, bg_data in BACKGROUNDS.items()
        if bg_data["category"] == category
    ]
