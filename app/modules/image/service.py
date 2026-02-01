"""
Service de traitement d'images pour Keroxio.
- Suppression arrière-plan via AutoBG.ai
- Application d'arrière-plans professionnels
- Ajout d'ombres et reflets
"""

import io
import uuid
import base64
import time
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from app.core.config import settings
from .backgrounds import BACKGROUNDS, get_background


class ImageService:
    """Service principal de traitement d'images."""
    
    def __init__(self):
        self.autobg_api_key = getattr(settings, 'AUTOBG_API_KEY', None)
        self.autobg_url = "https://www.autobg.ai/api"
        self.storage_path = Path(getattr(settings, 'STORAGE_PATH', '/tmp/storage'))
        self.storage_url = getattr(settings, 'STORAGE_URL', 'https://storage.keroxio.fr')
        
    async def _download_image(self, url: str) -> bytes:
        """Télécharge une image depuis une URL."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    
    async def _save_image(self, image: Image.Image, format: str = "PNG") -> str:
        """Sauvegarde une image et retourne l'URL."""
        output = io.BytesIO()
        
        if format.upper() == "JPEG":
            # Convertir en RGB si nécessaire (JPEG ne supporte pas alpha)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            image.save(output, format="JPEG", quality=92)
            ext = "jpg"
        else:
            image.save(output, format="PNG", optimize=True)
            ext = "png"
        
        output.seek(0)
        filename = f"{uuid.uuid4()}.{ext}"
        
        # Sauvegarder localement
        processed_path = self.storage_path / "processed"
        processed_path.mkdir(parents=True, exist_ok=True)
        file_path = processed_path / filename
        file_path.write_bytes(output.getvalue())
        
        return f"{self.storage_url}/processed/{filename}"

    async def remove_background(self, image_url: str) -> Dict[str, Any]:
        """
        Supprime l'arrière-plan d'une image via AutoBG.ai.
        
        Returns:
            Dict avec id, url de l'image transparente, temps de traitement
        """
        start = time.time()
        
        if not self.autobg_api_key:
            raise ValueError("AUTOBG_API_KEY non configurée")
        
        # Télécharger l'image source
        image_bytes = await self._download_image(image_url)
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Appel AutoBG.ai
        headers = {
            "Authorization": self.autobg_api_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "image": image_b64,
            "background": "transparent",
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.autobg_url}/remove-background",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()
        
        # Récupérer l'image résultat
        if "image" in result:
            processed_bytes = base64.b64decode(result["image"])
        elif "url" in result:
            processed_bytes = await self._download_image(result["url"])
        else:
            raise ValueError("Pas d'image dans la réponse AutoBG")
        
        # Sauvegarder
        image = Image.open(io.BytesIO(processed_bytes))
        processed_url = await self._save_image(image, "PNG")
        
        return {
            "id": str(uuid.uuid4()),
            "status": "completed",
            "original_url": image_url,
            "processed_url": processed_url,
            "processing_time": round(time.time() - start, 2),
        }

    def _create_gradient_background(
        self, 
        size: Tuple[int, int], 
        colors: list
    ) -> Image.Image:
        """Crée un fond en dégradé vertical."""
        width, height = size
        background = Image.new('RGB', size)
        draw = ImageDraw.Draw(background)
        
        # Parse colors
        from_color = self._hex_to_rgb(colors[0])
        to_color = self._hex_to_rgb(colors[1])
        
        for y in range(height):
            ratio = y / height
            r = int(from_color[0] + (to_color[0] - from_color[0]) * ratio)
            g = int(from_color[1] + (to_color[1] - from_color[1]) * ratio)
            b = int(from_color[2] + (to_color[2] - from_color[2]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        return background
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convertit une couleur hex en RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _add_shadow(
        self, 
        car_image: Image.Image, 
        opacity: float = 0.3,
        blur: int = 20,
        offset_y: int = 10
    ) -> Image.Image:
        """Ajoute une ombre sous la voiture."""
        # Créer l'ombre à partir de l'alpha channel
        if car_image.mode != 'RGBA':
            return car_image
        
        alpha = car_image.split()[-1]
        
        # Ombre = silhouette noire floue
        shadow = Image.new('RGBA', car_image.size, (0, 0, 0, 0))
        shadow_alpha = alpha.copy()
        
        # Réduire l'opacité
        shadow_alpha = shadow_alpha.point(lambda x: int(x * opacity))
        
        # Aplatir et flouter
        shadow.putalpha(shadow_alpha)
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
        
        # Décaler vers le bas
        shadow_offset = Image.new('RGBA', car_image.size, (0, 0, 0, 0))
        shadow_offset.paste(shadow, (0, offset_y))
        
        return shadow_offset

    def _add_reflection(
        self,
        car_image: Image.Image,
        opacity: float = 0.15,
        height_ratio: float = 0.3
    ) -> Image.Image:
        """Ajoute un reflet sous la voiture."""
        if car_image.mode != 'RGBA':
            return None
        
        # Flip vertical
        reflection = car_image.transpose(Image.FLIP_TOP_BOTTOM)
        
        # Réduire la hauteur
        new_height = int(car_image.height * height_ratio)
        reflection = reflection.crop((0, 0, reflection.width, new_height))
        
        # Appliquer un gradient d'opacité (plus transparent en bas)
        alpha = reflection.split()[-1]
        gradient = Image.new('L', reflection.size)
        draw = ImageDraw.Draw(gradient)
        
        for y in range(new_height):
            alpha_value = int(255 * opacity * (1 - y / new_height))
            draw.line([(0, y), (reflection.width, y)], fill=alpha_value)
        
        # Combiner les alphas
        new_alpha = Image.composite(
            alpha, 
            Image.new('L', alpha.size, 0),
            gradient
        )
        reflection.putalpha(new_alpha)
        
        return reflection

    async def apply_background(
        self,
        transparent_url: str,
        background_type: str = "showroom_indoor",
        custom_background_url: Optional[str] = None,
        scale: float = 1.0,
        position_x: float = 0.5,
        position_y: float = 0.7,
        add_shadow: bool = True,
        add_reflection: bool = False,
    ) -> Dict[str, Any]:
        """
        Applique un arrière-plan professionnel à une image transparente.
        
        Args:
            transparent_url: URL de l'image avec fond transparent
            background_type: Type de fond (voir backgrounds.py)
            custom_background_url: URL d'un fond custom
            scale: Échelle de la voiture (1.0 = 100%)
            position_x: Position horizontale (0-1)
            position_y: Position verticale (0-1)
            add_shadow: Ajouter une ombre
            add_reflection: Ajouter un reflet (style showroom)
        """
        start = time.time()
        
        # Charger l'image transparente
        car_bytes = await self._download_image(transparent_url)
        car_image = Image.open(io.BytesIO(car_bytes)).convert('RGBA')
        
        # Récupérer ou créer le fond
        bg_config = get_background(background_type)
        
        if background_type == "custom" and custom_background_url:
            # Fond custom
            bg_bytes = await self._download_image(custom_background_url)
            background = Image.open(io.BytesIO(bg_bytes)).convert('RGB')
        elif bg_config and "url" in bg_config:
            # Fond image
            bg_bytes = await self._download_image(bg_config["url"])
            background = Image.open(io.BytesIO(bg_bytes)).convert('RGB')
        elif bg_config and "gradient" in bg_config:
            # Fond dégradé
            background = self._create_gradient_background(
                (1920, 1080),  # Taille par défaut
                bg_config["gradient"]
            )
        elif bg_config and "color" in bg_config:
            # Fond couleur unie
            color = self._hex_to_rgb(bg_config["color"])
            background = Image.new('RGB', (1920, 1080), color)
        else:
            # Fallback: fond gris
            background = Image.new('RGB', (1920, 1080), (128, 128, 128))
        
        # Redimensionner le fond si nécessaire
        bg_width, bg_height = background.size
        
        # Appliquer l'échelle à la voiture
        if scale != 1.0:
            new_size = (int(car_image.width * scale), int(car_image.height * scale))
            car_image = car_image.resize(new_size, Image.LANCZOS)
        
        # Redimensionner la voiture pour qu'elle occupe ~60-70% de la largeur
        car_target_width = int(bg_width * 0.65)
        ratio = car_target_width / car_image.width
        car_image = car_image.resize(
            (car_target_width, int(car_image.height * ratio)),
            Image.LANCZOS
        )
        
        # Calculer la position
        car_x = int((bg_width - car_image.width) * position_x)
        car_y = int((bg_height - car_image.height) * position_y)
        
        # Ajouter l'ombre si demandé
        if add_shadow:
            shadow = self._add_shadow(car_image, opacity=0.25, blur=25, offset_y=15)
            background.paste(shadow, (car_x, car_y), shadow)
        
        # Ajouter le reflet si demandé
        if add_reflection:
            reflection = self._add_reflection(car_image, opacity=0.12, height_ratio=0.25)
            if reflection:
                refl_y = car_y + car_image.height
                if refl_y + reflection.height <= bg_height:
                    background.paste(reflection, (car_x, refl_y), reflection)
        
        # Coller la voiture
        background.paste(car_image, (car_x, car_y), car_image)
        
        # Sauvegarder
        processed_url = await self._save_image(background, "JPEG")
        
        return {
            "id": str(uuid.uuid4()),
            "status": "completed",
            "original_url": transparent_url,
            "background_type": background_type,
            "processed_url": processed_url,
            "processing_time": round(time.time() - start, 2),
        }

    async def process_complete(
        self,
        image_url: str,
        background_type: str = "showroom_indoor",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Pipeline complet: remove-bg + apply background.
        
        Combine les deux étapes en une seule.
        """
        start = time.time()
        
        # Étape 1: Remove background
        result_bg = await self.remove_background(image_url)
        
        # Étape 2: Apply background
        result_final = await self.apply_background(
            transparent_url=result_bg["processed_url"],
            background_type=background_type,
            **kwargs
        )
        
        result_final["original_url"] = image_url
        result_final["transparent_url"] = result_bg["processed_url"]
        result_final["processing_time"] = round(time.time() - start, 2)
        
        return result_final


# Singleton
_service: Optional[ImageService] = None

def get_image_service() -> ImageService:
    global _service
    if _service is None:
        _service = ImageService()
    return _service
