import os
import json
import re
import logging
import traceback
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)


def _generate_mock_outline(prompt: str, character_name: str, setting: str, tone: str, art_style: str) -> list[dict]:
    """Fallback 5-panel outline when Gemini API call fails or key is unconfigured."""
    return [
        {
            "panel_number": 1,
            "title": "The Awakening",
            "scene_description": f"Introduction to {character_name} in {setting}. A quiet moment before the adventure begins.",
            "image_prompt": f"Wide establishing shot of {character_name} standing in {setting}, {art_style} style, {tone} atmosphere, comic panel art, high detail, vibrant comic book colors, dynamic lighting.",
        },
        {
            "panel_number": 2,
            "title": "The Inciting Incident",
            "scene_description": f"{character_name} encounters an unexpected event related to '{prompt}' in {setting}.",
            "image_prompt": f"Medium shot of {character_name} noticing a startling clue or anomaly in {setting}, {art_style} style, {tone} mood, expressive face, cinematic framing, comic book illustration.",
        },
        {
            "panel_number": 3,
            "title": "The Rising Challenge",
            "scene_description": f"The situation intensifies. {character_name} must act quickly amidst rising stakes.",
            "image_prompt": f"Dynamic action panel of {character_name} facing an intense hurdle in {setting}, motion blur, dramatic angles, {art_style} style, {tone} energy, bold comic linework.",
        },
        {
            "panel_number": 4,
            "title": "The Climax",
            "scene_description": f"The decisive moment where {character_name} makes a bold choice to resolve the conflict.",
            "image_prompt": f"Heroic close-up climax shot of {character_name} unleashing their full courage in {setting}, high contrast lighting, {art_style} style, powerful composition, comic book masterpiece.",
        },
        {
            "panel_number": 5,
            "title": "The Resolution",
            "scene_description": f"The aftermath. {character_name} looks toward the horizon with new wisdom and strength.",
            "image_prompt": f"Scenic closing panel of {character_name} peaceful in {setting}, golden hour lighting, {art_style} aesthetic, {tone} feeling, cinematic wide lens comic panel.",
        },
    ]


def generate_outline(prompt: str, character_name: str, setting: str, tone: str, art_style: str) -> list[dict]:
    """
    Uses Gemini Flash (gemini-2.5-flash) to turn the story prompt into a structured 5-panel outline.
    Each panel is a dictionary with:
      - panel_number: int
      - title: str
      - scene_description: str
      - image_prompt: str
    Returns a list of 5 panel dicts.
    """
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    print(f"\n[gemini_flash] >>> GEMINI_API_KEY loaded: '{api_key[:6]}...' (length: {len(api_key)})")

    if not api_key or api_key == "your_gemini_api_key_here":
        print("[gemini_flash] WARNING: GEMINI_API_KEY is not configured or placeholder. Returning mock outline.")
        return _generate_mock_outline(prompt, character_name, setting, tone, art_style)

    try:
        genai.configure(api_key=api_key)

        system_instruction = (
            "You are a professional comic book storyboard artist and scriptwriter. "
            "Your task is to create a structured 5-panel comic strip outline. "
            "You must return ONLY a valid JSON array containing exactly 5 objects. "
            "Do not include any conversational preamble or postscript."
        )

        user_prompt = f"""
Create a compelling 5-panel comic strip outline based on these story elements:
- Story Prompt: {prompt}
- Main Character: {character_name}
- Setting: {setting}
- Tone: {tone}
- Art Style: {art_style}

Return a valid JSON array of exactly 5 panel objects. Each object must have these exact keys:
1. "panel_number": an integer from 1 to 5
2. "title": a short dramatic title for the panel
3. "scene_description": a vivid 2-3 sentence description of the visual scene, actions, and emotions
4. "image_prompt": a detailed Stable Diffusion text-to-image prompt optimized for {art_style} comic style, including visual framing (e.g. wide shot, close-up), character description, lighting, background details, and comic linework quality.

JSON Output:
"""
        models_to_try = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"]
        response = None
        last_err = None

        for model_name in models_to_try:
            try:
                print(f"[gemini_flash] Initiating API call to Gemini Flash ('{model_name}')...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    f"{system_instruction}\n\n{user_prompt}",
                    generation_config={"temperature": 0.7, "max_output_tokens": 3500, "response_mime_type": "application/json"}
                )
                print(f"[gemini_flash] SUCCESS with model '{model_name}'!")
                break
            except Exception as flash_err:
                print(f"[gemini_flash] '{model_name}' failed: {flash_err}. Trying next...")
                last_err = flash_err

        if response is None:
            raise last_err

        raw_text = response.text.strip() if hasattr(response, "text") and response.text else ""
        print(f"[gemini_flash] SUCCESS: Gemini Flash API call succeeded! Response length: {len(raw_text)}")

        # Clean JSON markdown fences if present
        clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
        clean_text = re.sub(r"\s*```$", "", clean_text, flags=re.MULTILINE).strip()

        # Extract array using regex if other text is included
        array_match = re.search(r"\[\s*\{.*\}\s*\]", clean_text, re.DOTALL)
        if array_match:
            clean_text = array_match.group(0)

        panels = json.loads(clean_text)

        if not isinstance(panels, list) or len(panels) == 0:
            raise ValueError(f"Parsed Gemini outline is not a non-empty list. Raw content: {raw_text[:200]}")

        # Ensure correct panel numbering and required fields
        normalized_panels = []
        for i, panel in enumerate(panels[:5], start=1):
            normalized_panels.append({
                "panel_number": panel.get("panel_number", i),
                "title": panel.get("title", f"Panel {i}"),
                "scene_description": panel.get("scene_description", "An eventful scene unfolds."),
                "image_prompt": panel.get("image_prompt", f"{character_name} in {setting}, {art_style} style, comic panel."),
            })

        while len(normalized_panels) < 5:
            idx = len(normalized_panels) + 1
            fallback_panel = _generate_mock_outline(prompt, character_name, setting, tone, art_style)[idx - 1]
            normalized_panels.append(fallback_panel)

        return normalized_panels

    except Exception as e:
        status_code = getattr(e, "code", getattr(e, "status_code", "N/A"))
        print(f"\n========================================================")
        print(f"[gemini_flash] !!! FULL EXCEPTION IN generate_outline !!!")
        print(f"Exception Type : {type(e).__name__}")
        print(f"Status Code    : {status_code}")
        print(f"Exception Message: {str(e)}")
        print(f"--- Full Traceback ---")
        traceback.print_exc()
        print(f"========================================================\n")
        print("[gemini_flash] Triggering fallback outline due to the exception above.")
        return _generate_mock_outline(prompt, character_name, setting, tone, art_style)
