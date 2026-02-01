"""
Service de traitement d'images Keroxio.
Option B: Remove-bg + Composite local avec Pillow.
"""

import asyncio
import httpx
import io
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image

from app.core.config import settings


class ImageService:
    """Service principal pour le traitement d'images."""
    
    def __init__(self):
        self.storage_path = Path(getattr(settings, 'STORAGE_PATH', '/tmp/storage'))
        # Use API URL for serving processed files directly
        self.api_url = "https://api.keroxio.fr"
        self.backgrounds_path = Path(__file__).parent / "backgrounds_images"
        
        # Create directories
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "processed").mkdir(exist_ok=True)
        
    # ========== REMOVE BACKGROUND ==========
    
    async def remove_background(
        self,
        image_bytes: bytes,
        method: str = "auto",
    ) -> bytes:
        """
        Supprime l'arrière-plan d'une image.
        
        Args:
            image_bytes: Image source en bytes
            method: "rembg" (local) ou "removebg" (API)
            
        Returns:
            PNG avec fond transparent
        """
        # Auto-select best available method
        if method == "auto":
            api_key = getattr(settings, 'REMOVEBG_API_KEY', None)
            if api_key:
                method = "removebg"
            else:
                method = "rembg"
        
        if method == "removebg":
            return await self._remove_bg_api(image_bytes)
        elif method == "rembg":
            return await self._remove_bg_rembg(image_bytes)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    async def _remove_bg_rembg(self, image_bytes: bytes) -> bytes:
        """Remove background using rembg (local ML model)."""
        try:
            from rembg import remove
            
            # Run in thread pool to not block async
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: remove(image_bytes)
            )
            return result
        except ImportError:
            raise RuntimeError("rembg not installed. Run: pip install rembg[gpu]")
    
    async def _remove_bg_api(self, image_bytes: bytes) -> bytes:
        """Remove background using remove.bg API."""
        api_key = getattr(settings, 'REMOVEBG_API_KEY', None)
        if not api_key:
            raise ValueError("REMOVEBG_API_KEY not configured")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": ("image.jpg", image_bytes, "image/jpeg")},
                data={"size": "auto"},
                headers={"X-Api-Key": api_key},
            )
            
            if response.status_code != 200:
                raise ValueError(f"remove.bg API error: {response.text}")
            
            return response.content
    
    # ========== COMPOSITE ==========
    
    async def composite(
        self,
        car_bytes: bytes,
        background_name: str,
        position: str = "center",
        scale: float = 0.85,
        vertical_offset: float = 0.0,
    ) -> bytes:
        """
        Compose une voiture (PNG transparent) sur un background.
        
        Args:
            car_bytes: PNG de la voiture avec fond transparent
            background_name: Nom du background (showroom, garage, etc.)
            position: Position de la voiture (center, left, right)
            scale: Échelle de la voiture (0.5-1.0)
            vertical_offset: Décalage vertical (-0.1 à 0.1, négatif = plus bas)
            
        Returns:
            Image JPG finale
        """
        # Load car image
        car_img = Image.open(io.BytesIO(car_bytes)).convert("RGBA")
        
        # Load background
        bg_path = self._get_background_path(background_name)
        if not bg_path.exists():
            raise ValueError(f"Background not found: {background_name}")
        
        bg_img = Image.open(bg_path).convert("RGBA")
        
        # Resize car to fit background
        car_img = self._resize_car(car_img, bg_img.size, scale)
        
        # Calculate position
        x, y = self._calculate_position(car_img.size, bg_img.size, position, vertical_offset)
        
        # Composite
        result = bg_img.copy()
        result.paste(car_img, (x, y), car_img)
        
        # Convert to RGB (no alpha) and save as JPG
        result_rgb = result.convert("RGB")
        output = io.BytesIO()
        result_rgb.save(output, format="JPEG", quality=92)
        return output.getvalue()
    
    def _get_background_path(self, name: str) -> Path:
        """Get background image path by name."""
        # Check in backgrounds_images folder
        for ext in [".jpg", ".jpeg", ".png"]:
            path = self.backgrounds_path / f"{name}{ext}"
            if path.exists():
                return path
        
        # Fallback to storage
        return self.storage_path / "backgrounds" / f"{name}.jpg"
    
    def _trim_transparent(self, img: Image.Image) -> Image.Image:
        """Trim transparent pixels from image edges."""
        if img.mode != "RGBA":
            return img
        
        # Get bounding box of non-transparent pixels
        bbox = img.getbbox()
        if bbox:
            return img.crop(bbox)
        return img
    
    def _resize_car(
        self,
        car: Image.Image,
        bg_size: Tuple[int, int],
        scale: float,
    ) -> Image.Image:
        """Resize car to fit background with smart auto-scaling.
        
        Adapts to car orientation:
        - Landscape (side view): scale based on width
        - Portrait (front/back view): scale based on height
        
        Scale 0.0 = auto (recommended)
        Scale 0.3-0.7 = manual override
        """
        # First trim transparent edges
        car = self._trim_transparent(car)
        
        bg_w, bg_h = bg_size
        car_w, car_h = car.size
        car_ratio = car_w / car_h
        
        # Auto-scale if scale is 0 or very small
        if scale <= 0.1:
            # Smart auto-scaling based on car orientation
            if car_ratio > 1.3:
                # Landscape car (side view) - fit to ~45% of width
                scale = 0.45
            elif car_ratio < 0.8:
                # Portrait car (front/back view) - fit to ~30% of height
                target_h = int(bg_h * 0.30)
                ratio = target_h / car_h
                target_w = int(car_w * ratio)
                return car.resize((target_w, target_h), Image.Resampling.LANCZOS)
            else:
                # Square-ish (3/4 view) - balanced at ~38%
                scale = 0.38
        
        # Width-based scaling
        target_w = int(bg_w * scale)
        ratio = target_w / car_w
        target_h = int(car_h * ratio)
        
        # Cap height at 50% of background
        if target_h > bg_h * 0.50:
            target_h = int(bg_h * 0.50)
            ratio = target_h / car_h
            target_w = int(car_w * ratio)
        
        return car.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    def _calculate_position(
        self,
        car_size: Tuple[int, int],
        bg_size: Tuple[int, int],
        position: str,
        vertical_offset: float = 0.0,
    ) -> Tuple[int, int]:
        """Calculate car position on background.
        
        Args:
            vertical_offset: Offset from bottom (negative = lower, positive = higher)
                            Value is percentage of bg height (-0.1 to 0.1 typical)
        """
        car_w, car_h = car_size
        bg_w, bg_h = bg_size
        
        # Vertical: bottom-aligned (car sits on "floor")
        # No margin - car touches the very bottom
        base_margin = 0  # Car sits at the bottom edge
        offset_pixels = int(bg_h * vertical_offset)
        y = bg_h - car_h - base_margin + offset_pixels
        
        # Horizontal
        if position == "left":
            x = int(bg_w * 0.05)
        elif position == "right":
            x = bg_w - car_w - int(bg_w * 0.05)
        else:  # center
            x = (bg_w - car_w) // 2
        
        return x, y
    
    # ========== FULL PROCESS ==========
    
    async def process_image(
        self,
        image_bytes: bytes,
        background_name: str,
        position: str = "center",
        scale: float = 0.85,
        vertical_offset: float = 0.0,
        remove_bg_method: str = "auto",
    ) -> Dict[str, Any]:
        """
        Pipeline complet: remove-bg + composite.
        
        Returns:
            Dict avec URLs des images
        """
        start = time.time()
        request_id = str(uuid.uuid4())
        
        # Step 1: Remove background
        car_transparent = await self.remove_background(
            image_bytes,
            method=remove_bg_method,
        )
        
        # Save transparent version
        transparent_filename = f"{request_id}_transparent.png"
        transparent_path = self.storage_path / "processed" / transparent_filename
        transparent_path.write_bytes(car_transparent)
        
        # Step 2: Composite with background
        final_image = await self.composite(
            car_transparent,
            background_name,
            position=position,
            scale=scale,
            vertical_offset=vertical_offset,
        )
        
        # Save final version
        final_filename = f"{request_id}_final.jpg"
        final_path = self.storage_path / "processed" / final_filename
        final_path.write_bytes(final_image)
        
        return {
            "id": request_id,
            "status": "completed",
            "transparent_url": f"{self.api_url}/image/files/{transparent_filename}",
            "final_url": f"{self.api_url}/image/files/{final_filename}",
            "background": background_name,
            "processing_time": round(time.time() - start, 2),
        }
    
    # ========== BACKGROUNDS MANAGEMENT ==========
    
    def list_backgrounds(self) -> List[Dict[str, Any]]:
        """Liste les backgrounds disponibles."""
        backgrounds = []
        
        # Check backgrounds_images folder
        if self.backgrounds_path.exists():
            for f in self.backgrounds_path.iterdir():
                if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    backgrounds.append({
                        "name": f.stem,
                        "filename": f.name,
                        "path": str(f),
                    })
        
        # Check storage/backgrounds folder
        storage_bg = self.storage_path / "backgrounds"
        if storage_bg.exists():
            for f in storage_bg.iterdir():
                if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    backgrounds.append({
                        "name": f.stem,
                        "filename": f.name,
                        "url": f"{self.api_url}/image/backgrounds/{f.name}",
                    })
        
        return backgrounds
    
    async def add_background(
        self,
        name: str,
        image_bytes: bytes,
    ) -> Dict[str, Any]:
        """Ajoute un nouveau background."""
        # Validate image
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
        except Exception as e:
            raise ValueError(f"Invalid image: {e}")
        
        # Save to storage
        bg_path = self.storage_path / "backgrounds"
        bg_path.mkdir(exist_ok=True)
        
        filename = f"{name}.jpg"
        filepath = bg_path / filename
        
        # Convert and save as JPG
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.save(filepath, format="JPEG", quality=95)
        
        return {
            "name": name,
            "filename": filename,
            "url": f"{self.api_url}/image/backgrounds/{filename}",
        }
    
    # ========== UTILITIES ==========
    
    async def download_image(self, url: str) -> bytes:
        """Download image from URL."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    
    def get_image_info(self, image_bytes: bytes) -> Dict[str, Any]:
        """Get image metadata."""
        img = Image.open(io.BytesIO(image_bytes))
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
            "size_bytes": len(image_bytes),
        }


# Singleton
_service: Optional[ImageService] = None

def get_image_service() -> ImageService:
    """Get or create ImageService singleton."""
    global _service
    if _service is None:
        _service = ImageService()
    return _service
