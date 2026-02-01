"""
Génère les backgrounds par défaut au démarrage si ils n'existent pas.
"""

from pathlib import Path
from PIL import Image, ImageDraw


def create_default_backgrounds(bg_dir: Path):
    """Crée les backgrounds de base pour Keroxio."""
    
    bg_dir.mkdir(parents=True, exist_ok=True)
    
    created = []
    
    # 1. Studio White - fond blanc épuré
    path = bg_dir / "studio_white.jpg"
    if not path.exists():
        img = Image.new('RGB', (1920, 1080), '#F5F5F5')
        draw = ImageDraw.Draw(img)
        # Gradient floor subtle
        for y in range(600, 1080):
            gray = int(245 - (y - 600) * 0.1)
            draw.line([(0, y), (1920, y)], fill=(gray, gray, gray))
        img.save(path, quality=95)
        created.append("studio_white")
    
    # 2. Studio Grey - fond gris neutre
    path = bg_dir / "studio_grey.jpg"
    if not path.exists():
        img = Image.new('RGB', (1920, 1080), '#E0E0E0')
        draw = ImageDraw.Draw(img)
        for y in range(600, 1080):
            gray = int(224 - (y - 600) * 0.15)
            draw.line([(0, y), (1920, y)], fill=(gray, gray, gray))
        img.save(path, quality=95)
        created.append("studio_grey")
    
    # 3. Studio Black - fond noir premium
    path = bg_dir / "studio_black.jpg"
    if not path.exists():
        img = Image.new('RGB', (1920, 1080), '#1A1A1A')
        draw = ImageDraw.Draw(img)
        for y in range(600, 1080):
            gray = int(26 + (y - 600) * 0.05)
            draw.line([(0, y), (1920, y)], fill=(gray, gray, gray))
        img.save(path, quality=95)
        created.append("studio_black")
    
    # 4. Showroom - effet showroom moderne
    path = bg_dir / "showroom.jpg"
    if not path.exists():
        img = Image.new('RGB', (1920, 1080), '#E8F4F8')
        draw = ImageDraw.Draw(img)
        # Sky gradient
        for y in range(700):
            r = int(232 - y * 0.02)
            g = int(244 - y * 0.015)
            b = int(248 - y * 0.01)
            draw.line([(0, y), (1920, y)], fill=(max(r, 150), max(g, 150), max(b, 160)))
        # Floor
        for y in range(700, 1080):
            gray = int(180 - (y - 700) * 0.1)
            draw.line([(0, y), (1920, y)], fill=(gray, gray, min(gray+5, 255)))
        img.save(path, quality=95)
        created.append("showroom")
    
    # 5. Garage Modern - sol époxy gris
    path = bg_dir / "garage_modern.jpg"
    if not path.exists():
        img = Image.new('RGB', (1920, 1080), '#2D2D2D')
        draw = ImageDraw.Draw(img)
        # Dark wall
        for y in range(500):
            gray = int(45 - y * 0.02)
            draw.line([(0, y), (1920, y)], fill=(max(gray, 30), max(gray, 30), max(gray, 32)))
        # Epoxy floor with slight reflection
        for y in range(500, 1080):
            base = int(60 + (y - 500) * 0.05)
            draw.line([(0, y), (1920, y)], fill=(base, base, base+2))
        img.save(path, quality=95)
        created.append("garage_modern")
    
    # 6. Outdoor - extérieur lumineux
    path = bg_dir / "outdoor.jpg"
    if not path.exists():
        img = Image.new('RGB', (1920, 1080), '#87CEEB')
        draw = ImageDraw.Draw(img)
        # Sky gradient (blue to white)
        for y in range(600):
            r = int(135 + y * 0.15)
            g = int(206 + y * 0.05)
            b = int(235 - y * 0.02)
            draw.line([(0, y), (1920, y)], fill=(min(r, 240), min(g, 245), max(b, 200)))
        # Ground (asphalt)
        for y in range(600, 1080):
            gray = int(100 - (y - 600) * 0.05)
            draw.line([(0, y), (1920, y)], fill=(max(gray, 60), max(gray, 60), max(gray, 60)))
        img.save(path, quality=95)
        created.append("outdoor")
    
    return created


def init():
    """Initialize backgrounds at startup."""
    bg_dir = Path(__file__).parent / "backgrounds_images"
    created = create_default_backgrounds(bg_dir)
    if created:
        print(f"[Image] Created default backgrounds: {', '.join(created)}")
    return len(created)
