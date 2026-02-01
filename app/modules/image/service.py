"""
Service de traitement d'images pour Keroxio.
- Suppression arrière-plan via AutoBG.ai
- Utilisation des backgrounds AutoBG intégrés
- Fallback: compositing local pour backgrounds custom
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


# Mapping de nos types vers les backgrounds AutoBG.ai
AUTOBG_BACKGROUNDS = {
    "transparent": "transparent",
    "studio_white": "white",
    "studio_grey": "grey",
    "studio_black": "black",
    # Showrooms AutoBG (IDs à confirmer avec leur API)
    "showroom_indoor": "showroom-indoor",
    "showroom_outdoor": "showroom-outdoor",
    "garage_modern": "garage-modern",
    "garage_luxury": "garage-luxury",
    "parking_outdoor": "outdoor",
}


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
        
        processed_path = self.storage_path / "processed"
        processed_path.mkdir(parents=True, exist_ok=True)
        file_path = processed_path / filename
        file_path.write_bytes(output.getvalue())
        
        return f"{self.storage_url}/processed/{filename}"
    
    async def _save_bytes(self, image_bytes: bytes, ext: str = "png") -> str:
        """Sauvegarde des bytes directement."""
        filename = f"{uuid.uuid4()}.{ext}"
        processed_path = self.storage_path / "processed"
        processed_path.mkdir(parents=True, exist_ok=True)
        file_path = processed_path / filename
        file_path.write_bytes(image_bytes)
        return f"{self.storage_url}/processed/{filename}"

    async def _call_autobg(
        self, 
        image_bytes: bytes, 
        background: str = "transparent"
    ) -> bytes:
        """
        Appelle l'API AutoBG.ai.
        
        Args:
            image_bytes: Image source en bytes
            background: Type de fond (transparent, white, showroom-indoor, etc.)
        
        Returns:
            Image résultat en bytes
        """
        if not self.autobg_api_key:
            raise ValueError("AUTOBG_API_KEY non configurée")
        
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        headers = {
            "Authorization": self.autobg_api_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "image": image_b64,
            "background": background,
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
            return base64.b64decode(result["image"])
        elif "url" in result:
            return await self._download_image(result["url"])
        else:
            raise ValueError("Pas d'image dans la réponse AutoBG")

    async def remove_background(self, image_url: str) -> Dict[str, Any]:
        """
        Supprime l'arrière-plan d'une image via AutoBG.ai.
        Retourne une image PNG transparente.
        """
        start = time.time()
        
        image_bytes = await self._download_image(image_url)
        result_bytes = await self._call_autobg(image_bytes, "transparent")
        
        processed_url = await self._save_bytes(result_bytes, "png")
        
        return {
            "id": str(uuid.uuid4()),
            "status": "completed",
            "original_url": image_url,
            "processed_url": processed_url,
            "processing_time": round(time.time() - start, 2),
        }

    async def apply_background(
        self,
        image_url: str,
        background_type: str = "showroom_indoor",
        custom_background_url: Optional[str] = None,
        scale: float = 1.0,
        position_x: float = 0.5,
        position_y: float = 0.7,
        add_shadow: bool = True,
        add_reflection: bool = False,
    ) -> Dict[str, Any]:
        """
        Applique un arrière-plan professionnel.
        
        Utilise AutoBG.ai directement si le background est supporté,
        sinon fait le compositing localement.
        """
        start = time.time()
        
        image_bytes = await self._download_image(image_url)
        
        # Vérifier si AutoBG supporte ce background
        autobg_bg = AUTOBG_BACKGROUNDS.get(background_type)
        
        if autobg_bg and background_type != "custom":
            # Utiliser AutoBG directement
            try:
                result_bytes = await self._call_autobg(image_bytes, autobg_bg)
                ext = "png" if background_type == "transparent" else "jpg"
                processed_url = await self._save_bytes(result_bytes, ext)
                
                return {
                    "id": str(uuid.uuid4()),
                    "status": "completed",
                    "original_url": image_url,
                    "background_type": background_type,
                    "background_source": "autobg",
                    "processed_url": processed_url,
                    "processing_time": round(time.time() - start, 2),
                }
            except Exception as e:
                # Fallback vers compositing local si AutoBG échoue
                print(f"AutoBG background failed, falling back to local: {e}")
        
        # Compositing local (pour custom ou fallback)
        # D'abord obtenir l'image transparente
        transparent_bytes = await self._call_autobg(image_bytes, "transparent")
        car_image = Image.open(io.BytesIO(transparent_bytes)).convert('RGBA')
        
        # Créer ou charger le background
        if background_type == "custom" and custom_background_url:
            bg_bytes = await self._download_image(custom_background_url)
            background = Image.open(io.BytesIO(bg_bytes)).convert('RGB')
        else:
            # Créer un fond par défaut (gradient gris)
            background = self._create_gradient_background((1920, 1080), ["#909090", "#606060"])
        
        # Redimensionner et positionner
        bg_width, bg_height = background.size
        car_target_width = int(bg_width * 0.65 * scale)
        ratio = car_target_width / car_image.width
        car_image = car_image.resize(
            (car_target_width, int(car_image.height * ratio)),
            Image.LANCZOS
        )
        
        car_x = int((bg_width - car_image.width) * position_x)
        car_y = int((bg_height - car_image.height) * position_y)
        
        # Ajouter ombre si demandé
        if add_shadow:
            shadow = self._add_shadow(car_image)
            background.paste(shadow, (car_x, car_y), shadow)
        
        # Coller la voiture
        background.paste(car_image, (car_x, car_y), car_image)
        
        processed_url = await self._save_image(background, "JPEG")
        
        return {
            "id": str(uuid.uuid4()),
            "status": "completed",
            "original_url": image_url,
            "background_type": background_type,
            "background_source": "local",
            "processed_url": processed_url,
            "processing_time": round(time.time() - start, 2),
        }

    async def process_with_autobg(
        self,
        image_url: str,
        background_type: str = "showroom_indoor",
    ) -> Dict[str, Any]:
        """
        Pipeline direct via AutoBG.ai.
        Utilise les backgrounds intégrés d'AutoBG.
        """
        start = time.time()
        
        image_bytes = await self._download_image(image_url)
        
        # Mapper vers le background AutoBG
        autobg_bg = AUTOBG_BACKGROUNDS.get(background_type, "showroom-indoor")
        
        result_bytes = await self._call_autobg(image_bytes, autobg_bg)
        
        ext = "png" if background_type == "transparent" else "jpg"
        processed_url = await self._save_bytes(result_bytes, ext)
        
        return {
            "id": str(uuid.uuid4()),
            "status": "completed",
            "original_url": image_url,
            "background_type": background_type,
            "autobg_background": autobg_bg,
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
        Pipeline complet: utilise AutoBG si possible.
        """
        # Essayer d'utiliser AutoBG directement
        if background_type in AUTOBG_BACKGROUNDS:
            return await self.process_with_autobg(image_url, background_type)
        
        # Sinon, compositing local
        return await self.apply_background(
            image_url=image_url,
            background_type=background_type,
            **kwargs
        )

    def _create_gradient_background(
        self, 
        size: Tuple[int, int], 
        colors: list
    ) -> Image.Image:
        """Crée un fond en dégradé vertical."""
        width, height = size
        background = Image.new('RGB', size)
        draw = ImageDraw.Draw(background)
        
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
        opacity: float = 0.25,
        blur: int = 25,
        offset_y: int = 15
    ) -> Image.Image:
        """Ajoute une ombre sous la voiture."""
        if car_image.mode != 'RGBA':
            return car_image
        
        alpha = car_image.split()[-1]
        shadow = Image.new('RGBA', car_image.size, (0, 0, 0, 0))
        shadow_alpha = alpha.copy()
        shadow_alpha = shadow_alpha.point(lambda x: int(x * opacity))
        shadow.putalpha(shadow_alpha)
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
        
        shadow_offset = Image.new('RGBA', car_image.size, (0, 0, 0, 0))
        shadow_offset.paste(shadow, (0, offset_y))
        
        return shadow_offset

    async def list_autobg_backgrounds(self) -> Dict[str, Any]:
        """Liste les backgrounds disponibles via AutoBG."""
        return {
            "autobg_supported": list(AUTOBG_BACKGROUNDS.keys()),
            "mapping": AUTOBG_BACKGROUNDS,
            "note": "Ces backgrounds utilisent directement l'API AutoBG.ai",
        }


# Singleton
_service: Optional[ImageService] = None

def get_image_service() -> ImageService:
    global _service
    if _service is None:
        _service = ImageService()
    return _service
