"""
Service de traitement d'images pour Keroxio.
Intégration AutoBG.ai API v1

Flow:
1. Créer des templates avec backgrounds
2. Uploader images avec template
3. Poll status jusqu'à completion
4. Récupérer image résultat
"""

import io
import uuid
import base64
import time
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx
from PIL import Image

from app.core.config import settings


class AutoBGService:
    """Client pour l'API AutoBG.ai."""
    
    BASE_URL = "https://apis.autobg.ai/public/api/v1"
    
    def __init__(self):
        self.api_key = getattr(settings, 'AUTOBG_API_KEY', None)
        self.storage_path = Path(getattr(settings, 'STORAGE_PATH', '/tmp/storage'))
        self.storage_url = getattr(settings, 'STORAGE_URL', 'https://storage.keroxio.fr')
        self._templates_cache: Dict[str, int] = {}
    
    def _headers(self) -> Dict[str, str]:
        """Headers pour les requêtes AutoBG."""
        return {"Authorization": self.api_key}
    
    async def _save_bytes(self, image_bytes: bytes, ext: str = "jpg") -> str:
        """Sauvegarde des bytes et retourne l'URL."""
        filename = f"{uuid.uuid4()}.{ext}"
        processed_path = self.storage_path / "processed"
        processed_path.mkdir(parents=True, exist_ok=True)
        file_path = processed_path / filename
        file_path.write_bytes(image_bytes)
        return f"{self.storage_url}/processed/{filename}"

    # ========== TEMPLATES ==========
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """Liste les templates existants."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/templates/list",
                headers=self._headers(),
            )
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, dict) and result.get("status"):
                data = result.get("data", {})
                if isinstance(data, dict):
                    return data.get("templates", [])
                return data if isinstance(data, list) else []
            elif isinstance(result, list):
                return result
            return []
    
    async def create_template(
        self,
        name: str,
        background_file: bytes,
        side_file: Optional[bytes] = None,
        front_rear_file: Optional[bytes] = None,
        number_plate_file: Optional[bytes] = None,
        brand_logo_file: Optional[bytes] = None,
        num_plate: bool = False,
        brand_alignment: str = "TR",  # TL=Top Left, TR=Top Right
    ) -> int:
        """
        Crée un template AutoBG.
        
        Returns:
            templateID
        """
        files = {
            "background": ("background.jpg", background_file, "image/jpeg"),
        }
        
        if side_file:
            files["side"] = ("side.jpg", side_file, "image/jpeg")
        if front_rear_file:
            files["frontRear"] = ("front_rear.jpg", front_rear_file, "image/jpeg")
        if number_plate_file:
            files["numberPlate"] = ("number_plate.png", number_plate_file, "image/png")
        if brand_logo_file:
            files["brandLogo"] = ("logo.png", brand_logo_file, "image/png")
        
        data = {
            "name": name,
            "numPlate": str(num_plate).lower(),
            "bAlignment": brand_alignment,
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/templates/create",
                headers=self._headers(),
                files=files,
                data=data,
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("status"):
                template_id = result.get("data", {}).get("templateID")
                self._templates_cache[name] = template_id
                return template_id
            else:
                raise ValueError(f"Template creation failed: {result.get('message')}")

    async def get_or_create_template(
        self,
        name: str,
        background_url: str,
    ) -> int:
        """Récupère ou crée un template."""
        # Check cache
        if name in self._templates_cache:
            return self._templates_cache[name]
        
        # List existing templates
        try:
            templates = await self.list_templates()
            for t in templates:
                if isinstance(t, dict):
                    t_name = t.get("name") or t.get("templateName") or ""
                    t_id = t.get("id") or t.get("templateID")
                    if t_name == name and t_id:
                        self._templates_cache[name] = t_id
                        return t_id
        except Exception as e:
            print(f"Error listing templates: {e}")
        
        # Create new template
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(background_url)
            response.raise_for_status()
            background_bytes = response.content
        
        return await self.create_template(name, background_bytes)

    # ========== IMAGE PROCESSING ==========
    
    async def upload_image_without_template(
        self,
        image_bytes: bytes,
        batch_id: str,
        hide_plate: bool = False,
        process_type: str = "ai",  # "ai" or "collab"
    ) -> Dict[str, Any]:
        """
        Upload une image sans template (remove-bg seulement).
        
        Args:
            image_bytes: Image de la voiture
            batch_id: Identifiant unique pour ce batch
            hide_plate: True pour masquer la plaque
            process_type: "ai" (instant) ou "collab" (QA humain)
        
        Returns:
            Dict avec batchID et images info
        """
        files = {
            "cc": ("car.jpg", image_bytes, "image/jpeg"),
        }
        data = {
            "numberPlate": batch_id,
            "numPlateProcessor": "1" if hide_plate else "0",
            "processType": process_type,
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/images/uploadWithoutTemplateCC",
                headers=self._headers(),
                files=files,
                data=data,
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("status"):
                return result.get("data", {})
            else:
                raise ValueError(f"Upload failed: {result.get('message')}")
    
    async def upload_image_with_template(
        self,
        image_bytes: bytes,
        template_id: int,
        batch_id: str,
        hide_plate: bool = False,
        process_type: str = "ai",
    ) -> Dict[str, Any]:
        """
        Upload une image avec un template (background + processing).
        """
        files = {
            "cc": ("car.jpg", image_bytes, "image/jpeg"),
        }
        data = {
            "templateID": str(template_id),
            "numberPlate": batch_id,
            "numPlateProcessor": "1" if hide_plate else "0",
            "processType": process_type,
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/images/uploadWithTemplateCC",
                headers=self._headers(),
                files=files,
                data=data,
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("status"):
                return result.get("data", {})
            else:
                raise ValueError(f"Upload failed: {result.get('message')}")
    
    async def get_image_status(self, batch_id: str) -> Dict[str, Any]:
        """Vérifie le status d'un batch d'images."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/images/imagesStatus",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"batchID": batch_id},
            )
            response.raise_for_status()
            return response.json()
    
    async def get_image_base64(self, pic_id: int) -> str:
        """Récupère l'image traitée en base64."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/images/getImagesBase64",
                headers=self._headers(),
                params={"picID": str(pic_id)},
            )
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, dict) and result.get("status"):
                return result.get("data", {}).get("image", "")
            elif isinstance(result, str):
                return result
            else:
                raise ValueError(f"Get image failed: {result}")
    
    async def get_image_raw(self, pic_id: int) -> bytes:
        """Récupère l'image traitée en bytes."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/images/getImagesRaw",
                headers=self._headers(),
                params={"picID": str(pic_id)},
            )
            response.raise_for_status()
            return response.content
    
    async def wait_for_processing(
        self,
        batch_id: str,
        timeout: int = 120,
        poll_interval: int = 3,
    ) -> Dict[str, Any]:
        """
        Attend que le batch soit traité.
        
        Returns:
            Dict avec les infos des images traitées, ou None si échec
        """
        start = time.time()
        while time.time() - start < timeout:
            try:
                status = await self.get_image_status(batch_id)
                if status.get("status"):
                    data = status.get("data", {})
                    images = data.get("images", [])
                    
                    # Vérifier si toutes les images sont traitées
                    if images:
                        all_done = True
                        for img in images:
                            img_status = img.get("status", "").lower()
                            if img_status in ["pending", "processing", "queued"]:
                                all_done = False
                                break
                            elif img_status in ["failed", "error"]:
                                return None
                        
                        if all_done:
                            return data
            except Exception as e:
                print(f"Status check error: {e}")
            
            await asyncio.sleep(poll_interval)
        return None


class ImageService:
    """Service principal de traitement d'images."""
    
    def __init__(self):
        self.autobg = AutoBGService()
        self.storage_path = Path(getattr(settings, 'STORAGE_PATH', '/tmp/storage'))
        self.storage_url = getattr(settings, 'STORAGE_URL', 'https://storage.keroxio.fr')
    
    async def _download_image(self, url: str) -> bytes:
        """Télécharge une image depuis une URL."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    
    async def _save_bytes(self, image_bytes: bytes, ext: str = "jpg") -> str:
        """Sauvegarde des bytes et retourne l'URL."""
        filename = f"{uuid.uuid4()}.{ext}"
        processed_path = self.storage_path / "processed"
        processed_path.mkdir(parents=True, exist_ok=True)
        file_path = processed_path / filename
        file_path.write_bytes(image_bytes)
        return f"{self.storage_url}/processed/{filename}"

    async def remove_background(
        self,
        image_url: str,
        hide_plate: bool = False,
    ) -> Dict[str, Any]:
        """
        Supprime l'arrière-plan via AutoBG.ai (sans template).
        """
        start = time.time()
        
        # Download image
        image_bytes = await self._download_image(image_url)
        
        # Generate unique batch ID
        batch_id = f"keroxio-{uuid.uuid4().hex[:8]}"
        
        # Upload to AutoBG
        result = await self.autobg.upload_image_without_template(
            image_bytes=image_bytes,
            batch_id=batch_id,
            hide_plate=hide_plate,
            process_type="ai",
        )
        
        # Get batch ID from response (might be different)
        autobg_batch_id = result.get("batchID") or batch_id
        images = result.get("images", [])
        
        if not images:
            raise ValueError("No images in response")
        
        # Get pic ID from first image
        pic_id = images[0].get("picID") or images[0].get("id")
        
        # Wait for processing using batch ID
        status_data = await self.autobg.wait_for_processing(str(autobg_batch_id))
        if not status_data:
            raise ValueError("Image processing failed or timed out")
        
        # Get pic ID from status if available
        status_images = status_data.get("images", [])
        if status_images:
            pic_id = status_images[0].get("picID") or status_images[0].get("id") or pic_id
        
        # Get processed image
        processed_bytes = await self.autobg.get_image_raw(pic_id)
        processed_url = await self._save_bytes(processed_bytes, "png")
        
        return {
            "id": str(uuid.uuid4()),
            "status": "completed",
            "original_url": image_url,
            "processed_url": processed_url,
            "autobg_batch_id": autobg_batch_id,
            "autobg_pic_id": pic_id,
            "processing_time": round(time.time() - start, 2),
        }

    async def process_with_template(
        self,
        image_url: str,
        template_name: str,
        background_url: str,
        hide_plate: bool = False,
    ) -> Dict[str, Any]:
        """
        Traite une image avec un template AutoBG.
        """
        start = time.time()
        
        # Get or create template
        template_id = await self.autobg.get_or_create_template(
            name=template_name,
            background_url=background_url,
        )
        
        # Download car image
        image_bytes = await self._download_image(image_url)
        
        # Generate unique batch ID
        batch_id = f"keroxio-{uuid.uuid4().hex[:8]}"
        
        # Upload with template
        result = await self.autobg.upload_image_with_template(
            image_bytes=image_bytes,
            template_id=template_id,
            batch_id=batch_id,
            hide_plate=hide_plate,
            process_type="ai",
        )
        
        # Get batch ID and pic ID from response
        autobg_batch_id = result.get("batchID") or batch_id
        images = result.get("images", [])
        
        if not images:
            raise ValueError("No images in response")
        
        pic_id = images[0].get("picID") or images[0].get("id")
        
        # Wait for processing using batch ID
        status_data = await self.autobg.wait_for_processing(str(autobg_batch_id))
        if not status_data:
            raise ValueError("Image processing failed or timed out")
        
        # Get pic ID from status if available
        status_images = status_data.get("images", [])
        if status_images:
            pic_id = status_images[0].get("picID") or status_images[0].get("id") or pic_id
        
        # Get processed image
        processed_bytes = await self.autobg.get_image_raw(pic_id)
        processed_url = await self._save_bytes(processed_bytes, "jpg")
        
        return {
            "id": str(uuid.uuid4()),
            "status": "completed",
            "original_url": image_url,
            "processed_url": processed_url,
            "template_name": template_name,
            "template_id": template_id,
            "autobg_batch_id": autobg_batch_id,
            "autobg_pic_id": pic_id,
            "processing_time": round(time.time() - start, 2),
        }

    async def list_templates(self) -> List[Dict[str, Any]]:
        """Liste les templates AutoBG disponibles."""
        return await self.autobg.list_templates()

    async def get_credits(self) -> Dict[str, Any]:
        """Récupère les crédits restants."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.autobg.BASE_URL}/user/credits",
                headers=self.autobg._headers(),
            )
            response.raise_for_status()
            return response.json()


# Singleton
_service: Optional[ImageService] = None

def get_image_service() -> ImageService:
    global _service
    if _service is None:
        _service = ImageService()
    return _service
