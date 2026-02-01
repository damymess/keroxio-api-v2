"""
Module Image - Traitement d'images Keroxio.

Features:
- Remove background (rembg local ML)
- Composite avec backgrounds professionnels
- Pipeline complet remove-bg + composite
"""

from .router import router

# Initialize default backgrounds at import
try:
    from .init_backgrounds import init
    init()
except Exception as e:
    print(f"[Image] Warning: Could not initialize backgrounds: {e}")

__all__ = ["router"]
