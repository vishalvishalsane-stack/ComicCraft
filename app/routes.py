import os
import logging
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf

logger = logging.getLogger(__name__)

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


class PromptRequest(BaseModel):
    story_prompt: str = Field(..., description="Main story idea or synopsis")
    character_name: str = Field(..., description="Protagonist or main character name")
    setting: str = Field(..., description="Setting or location (e.g. forest, school, space)")
    story_tone: str = Field(..., description="Story tone (e.g. dramatic, funny, poetic, light-hearted)")
    art_style: str = Field(..., description="Art style (e.g. anime, pixel art, comic book, realistic)")


class TestImageRequest(BaseModel):
    prompt: str = Field(..., description="Custom image generation prompt")
    art_style: Optional[str] = Field("comic book", description="Art style for the image")


@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Renders the homepage form."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@router.post("/generate", response_class=HTMLResponse)
async def post_generate(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    story_tone: str = Form(...),
    art_style: str = Form(...),
):
    """
    Reads form fields via Form(...), executes the full ComicCraft pipeline:
    generate_outline -> generate_story -> generate_image per panel ->
    build_comic_layout -> save_pdf -> renders comic_preview.html
    """
    try:
        logger.info(f"Generating comic for '{character_name}' in '{setting}' with tone '{story_tone}' and style '{art_style}'")

        # 1. Generate 5-panel outline using Gemini Flash
        outline = generate_outline(
            prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=story_tone,
            art_style=art_style,
        )

        # 2. Generate full narration and dialogue using Gemini Pro
        story_text = generate_story(
            outline=outline,
            character_name=character_name,
            setting=setting,
            tone=story_tone,
        )

        # 3. Generate panel images using Stable Diffusion / image generator
        image_paths = []
        for panel in outline:
            p_prompt = panel.get("image_prompt", f"{character_name} in {setting}")
            img_path = generate_image(prompt=p_prompt, art_style=art_style)
            image_paths.append(img_path)

        # 4. Build comic layout merging story and imagery
        layout = build_comic_layout(
            outline=outline,
            story_text=story_text,
            image_paths=image_paths,
        )

        # 5. Compile and export multi-page PDF
        comic_title = f"{character_name}'s Quest in {setting}"
        pdf_path = save_pdf(layout=layout, title=comic_title)

        # 6. Render comic preview
        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "pdf_path": pdf_path,
                "comic_title": comic_title,
                "character_name": character_name,
                "setting": setting,
                "story_tone": story_tone,
                "art_style": art_style,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during comic generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Comic generation failed: {str(e)}"
        )


@router.post("/generate-comic/json")
async def post_generate_json(payload: PromptRequest):
    """
    Accepts JSON body validated via PromptRequest Pydantic model,
    runs the same generation pipeline as /generate,
    returns JSON with layout data + PDF path.
    """
    try:
        logger.info(f"JSON Request received for '{payload.character_name}'")

        # 1. Outline
        outline = generate_outline(
            prompt=payload.story_prompt,
            character_name=payload.character_name,
            setting=payload.setting,
            tone=payload.story_tone,
            art_style=payload.art_style,
        )

        # 2. Story text
        story_text = generate_story(
            outline=outline,
            character_name=payload.character_name,
            setting=payload.setting,
            tone=payload.story_tone,
        )

        # 3. Images
        image_paths = []
        for panel in outline:
            p_prompt = panel.get("image_prompt", f"{payload.character_name} in {payload.setting}")
            img_path = generate_image(prompt=p_prompt, art_style=payload.art_style)
            image_paths.append(img_path)

        # 4. Layout
        layout = build_comic_layout(
            outline=outline,
            story_text=story_text,
            image_paths=image_paths,
        )

        # 5. PDF Export
        comic_title = f"{payload.character_name}'s Quest in {payload.setting}"
        pdf_path = save_pdf(layout=layout, title=comic_title)

        return {
            "status": "success",
            "comic_title": comic_title,
            "layout": layout,
            "pdf_path": pdf_path,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during JSON comic generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Comic generation failed: {str(e)}"
        )


@router.get("/export-success", response_class=HTMLResponse)
async def get_export_success(request: Request, pdf_path: Optional[str] = "", title: Optional[str] = "Your Comic"):
    """Renders export_success.html."""
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_path": pdf_path,
            "title": title,
        }
    )


@router.post("/test-image")
async def post_test_image(payload: TestImageRequest):
    """
    Calls generate_image() directly with a custom prompt, for testing only.
    """
    try:
        if not payload.prompt or not payload.prompt.strip():
            raise HTTPException(status_code=400, detail="Missing required field 'prompt'.")

        art_style = payload.art_style or "comic book"
        image_path = generate_image(prompt=payload.prompt, art_style=art_style)
        return {
            "status": "success",
            "prompt": payload.prompt,
            "art_style": art_style,
            "image_path": image_path,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing image generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {str(e)}"
        )
