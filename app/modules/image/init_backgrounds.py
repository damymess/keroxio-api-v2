"""
Background initialization - disabled (using custom uploads only).
"""

from pathlib import Path


def create_default_backgrounds(bg_dir: Path):
    """Disabled - backgrounds are uploaded manually."""
    bg_dir.mkdir(parents=True, exist_ok=True)
    return []


def init():
    """Initialize backgrounds directory (no defaults)."""
    bg_dir = Path(__file__).parent / "backgrounds_images"
    bg_dir.mkdir(parents=True, exist_ok=True)
    print("[Image] Backgrounds directory ready (no defaults - upload your own)")
    return 0
