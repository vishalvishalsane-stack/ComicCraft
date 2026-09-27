import os
from dotenv import load_dotenv

# Load env variables first so custom HF_HOME in .env is honored
load_dotenv(override=True)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_default_cache = "D:/huggingface_cache" if os.path.exists("D:/huggingface_cache") else os.path.join(PROJECT_ROOT, "huggingface_cache")
os.environ["HF_HOME"] = os.getenv("HF_HOME", _default_cache)

import time
import re
import uuid
import logging
import traceback
from PIL import Image, ImageDraw
import torch
from diffusers import StableDiffusionPipeline

logger = logging.getLogger(__name__)

# Base directory for storing generated panels
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PANELS_DIR = os.path.join(BASE_DIR, "static", "panels")
os.makedirs(PANELS_DIR, exist_ok=True)

# Determine compute device and precision
_device = "cuda" if torch.cuda.is_available() else "cpu"
_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

if _device == "cpu":
    print("\n" + "=" * 60)
    print("[image_generator] WARNING: CUDA is not available.")
    print("[image_generator] Running Stable Diffusion locally on CPU (generation will be slower).")
    print("=" * 60 + "\n")

# Load pipeline ONCE at module level
print(f"[image_generator] Initializing local Stable Diffusion pipeline ('runwayml/stable-diffusion-v1-5') on {_device}...")
print(f"[image_generator] Model cache directory: {os.environ.get('HF_HOME')}")
_load_start = time.time()

try:
    _pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=_dtype,
        safety_checker=None
    )
    _pipe = _pipe.to(_device)
    if _device == "cpu":
        _pipe.enable_attention_slicing()
    _load_time = time.time() - _load_start
    print(f"[image_generator] SUCCESS: Local Stable Diffusion pipeline loaded in {_load_time:.2f}s on {_device}!\n")
except Exception as _load_err:
    print(f"[image_generator] ERROR loading local pipeline: {_load_err}")
    traceback.print_exc()
    _pipe = None


def sanitize_filename(prompt: str) -> str:
    """Sanitize prompt to create a filesystem-safe filename."""
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", prompt[:30]).strip("_")
    if not clean:
        clean = "comic_panel"
    uid = uuid.uuid4().hex[:6]
    timestamp = int(time.time())
    return f"{clean}_{timestamp}_{uid}.png"


def _generate_stylized_comic_panel(prompt: str, art_style: str = "comic book") -> Image.Image:
    """
    Creates a high-contrast, stylish comic-book visual panel with borders,
    halftone/speedlines effect, comic banner, and artistic typography.
    Used only if local generation encounters an unexpected error.
    """
    width, height = 512, 512
    img = Image.new("RGB", (width, height), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)

    palette = {
        "anime": ((255, 182, 193), (135, 206, 250), (255, 105, 180)),
        "pixel art": ((44, 62, 80), (52, 152, 219), (231, 76, 60)),
        "comic book": ((255, 223, 0), (230, 40, 40), (20, 40, 160)),
        "realistic": ((70, 80, 95), (140, 150, 165), (20, 25, 35)),
    }
    bg_start, bg_mid, accent = palette.get(art_style.lower(), ((255, 215, 0), (235, 75, 55), (30, 60, 180)))

    for y in range(height):
        ratio = y / height
        r = int(bg_start[0] * (1 - ratio) + bg_mid[0] * ratio)
        g = int(bg_start[1] * (1 - ratio) + bg_mid[1] * ratio)
        b = int(bg_start[2] * (1 - ratio) + bg_mid[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    cx, cy = width // 2, height // 2 - 20
    import math
    num_rays = 28
    for i in range(num_rays):
        if i % 2 == 0:
            angle1 = (2 * math.pi / num_rays) * i
            angle2 = (2 * math.pi / num_rays) * (i + 0.6)
            ray_poly = [
                (cx, cy),
                (cx + int(width * 1.5 * math.cos(angle1)), cy + int(height * 1.5 * math.sin(angle1))),
                (cx + int(width * 1.5 * math.cos(angle2)), cy + int(height * 1.5 * math.sin(angle2))),
            ]
            draw.polygon(ray_poly, fill=(255, 255, 255, 90))

    for x in range(20, width - 20, 24):
        for y in range(20, height - 20, 24):
            draw.ellipse([x, y, x + 3, y + 3], fill=(255, 255, 255, 120))

    inner_margin = 28
    draw.rectangle(
        [inner_margin, inner_margin, width - inner_margin, height - inner_margin],
        outline=(20, 20, 20),
        width=5
    )

    emblem_w, emblem_h = 360, 160
    ex1 = (width - emblem_w) // 2
    ey1 = (height - emblem_h) // 2 - 20
    draw.rectangle([ex1 + 6, ey1 + 6, ex1 + emblem_w + 6, ey1 + emblem_h + 6], fill=(15, 15, 15))
    draw.rectangle([ex1, ey1, ex1 + emblem_w, ey1 + emblem_h], fill=(255, 255, 255), outline=(20, 20, 20), width=4)

    badge_text = f"★ {art_style.upper()} ART PANEL ★"
    draw.rectangle([ex1 + 20, ey1 - 16, ex1 + emblem_w - 20, ey1 + 14], fill=accent, outline=(20, 20, 20), width=2)
    draw.text((ex1 + 45, ey1 - 14), badge_text, fill=(255, 255, 255))

    words = prompt.split()
    line1 = " ".join(words[:5])
    line2 = " ".join(words[5:11]) if len(words) > 5 else ""
    line3 = " ".join(words[11:17]) if len(words) > 11 else ""

    draw.text((ex1 + 20, ey1 + 35), line1, fill=(20, 20, 20))
    if line2:
        draw.text((ex1 + 20, ey1 + 65), line2, fill=(40, 40, 40))
    if line3:
        draw.text((ex1 + 20, ey1 + 95), line3, fill=(60, 60, 60))

    draw.rectangle([inner_margin + 10, height - inner_margin - 36, width - inner_margin - 10, height - inner_margin - 8], fill=(20, 20, 20))
    draw.text((inner_margin + 20, height - inner_margin - 30), "COMICCRAFT • AI GENERATED PANEL", fill=(255, 215, 0))

    draw.rectangle([0, 0, width - 1, height - 1], outline=(15, 15, 15), width=8)

    return img


def generate_image(prompt: str, art_style: str = "comic book") -> str:
    """
    Uses the locally loaded Stable Diffusion pipeline (100% offline, zero cloud API calls)
    to generate a comic panel image. Saves to static/panels/ and returns the web file path.
    """
    filename = sanitize_filename(prompt)
    disk_path = os.path.join(PANELS_DIR, filename)
    relative_web_path = f"/static/panels/{filename}"

    enhanced_prompt = f"{prompt}, {art_style} art style, comic book illustration, crisp linework, highly detailed, vibrant colors, comic panel, 8k resolution"

    if _pipe is not None:
        try:
            gen_start = time.time()
            steps = 15 if _device == "cpu" else 25
            print(f"\n[image_generator] Generating real local image on {_device} ({steps} inference steps)...")
            print(f"[image_generator] Prompt: '{prompt[:65]}...'")

            # Run local inference
            image = _pipe(enhanced_prompt, num_inference_steps=steps).images[0]
            image.save(disk_path)
            gen_time = time.time() - gen_start

            print(f"[image_generator] SUCCESS: Real local image generated in {gen_time:.2f}s and saved to {disk_path}")
            return relative_web_path

        except Exception as e:
            print(f"\n[image_generator] FULL EXCEPTION during local generation: {type(e).__name__}: {e}")
            traceback.print_exc()

    # Fallback placeholder if local pipeline wasn't loaded or threw an exception
    print(f"[image_generator] Fallback: Generating stylized comic placeholder for '{prompt[:40]}...'")
    panel_img = _generate_stylized_comic_panel(prompt, art_style=art_style)
    panel_img.save(disk_path, format="PNG")
    print(f"[image_generator] Fallback placeholder saved to {disk_path}")

    return relative_web_path
