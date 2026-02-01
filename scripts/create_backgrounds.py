"""
Generate studio backgrounds for Keroxio.
Creates solid color and gradient backgrounds.
"""

from PIL import Image, ImageDraw
from pathlib import Path


def create_gradient(size, color1, color2, direction="vertical"):
    """Create a gradient image."""
    width, height = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    
    if direction == "vertical":
        for y in range(height):
            ratio = y / height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    else:
        for x in range(width):
            ratio = x / width
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(x, 0), (x, height)], fill=(r, g, b))
    
    return img


def add_floor_reflection(img, floor_ratio=0.3, darken=0.15):
    """Add a subtle floor reflection zone at the bottom."""
    width, height = img.size
    floor_height = int(height * floor_ratio)
    
    # Create overlay for floor darkening
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for y in range(height - floor_height, height):
        progress = (y - (height - floor_height)) / floor_height
        alpha = int(255 * darken * progress)
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    
    # Composite
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    return result.convert("RGB")


def create_backgrounds(output_dir: Path):
    """Generate all studio backgrounds."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Standard size (16:9 landscape)
    size = (1920, 1080)
    
    backgrounds = {
        # Studio blanc - clean white with subtle gradient
        "studio_white": {
            "gradient": [(255, 255, 255), (240, 240, 240)],
            "floor": True,
        },
        # Studio gris - neutral grey
        "studio_grey": {
            "gradient": [(160, 160, 160), (100, 100, 100)],
            "floor": True,
        },
        # Studio noir - premium black
        "studio_black": {
            "gradient": [(50, 50, 55), (15, 15, 18)],
            "floor": True,
        },
        # Showroom bleu moderne
        "showroom": {
            "gradient": [(45, 55, 72), (25, 30, 42)],
            "floor": True,
        },
        # Garage moderne - dark with warm tones
        "garage_modern": {
            "gradient": [(55, 50, 48), (30, 28, 26)],
            "floor": True,
        },
        # Outdoor - sky gradient
        "outdoor": {
            "gradient": [(135, 170, 200), (200, 210, 220)],
            "floor": False,
        },
    }
    
    created = []
    
    for name, config in backgrounds.items():
        print(f"Creating {name}...")
        
        # Create gradient
        img = create_gradient(size, config["gradient"][0], config["gradient"][1])
        
        # Add floor effect if specified
        if config.get("floor"):
            img = add_floor_reflection(img)
        
        # Save
        filepath = output_dir / f"{name}.jpg"
        img.save(filepath, "JPEG", quality=95)
        created.append(filepath)
        print(f"  OK: {filepath}")
    
    return created


if __name__ == "__main__":
    # Create in module's backgrounds_images folder
    module_dir = Path(__file__).parent.parent / "app" / "modules" / "image" / "backgrounds_images"
    
    print("=" * 50)
    print("Creating Keroxio Backgrounds")
    print("=" * 50)
    
    created = create_backgrounds(module_dir)
    
    print()
    print(f"[OK] Created {len(created)} backgrounds in:")
    print(f"   {module_dir}")
