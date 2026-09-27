import os
import logging
import traceback
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)


def _generate_mock_story(outline: list[dict], character_name: str, setting: str, tone: str) -> str:
    """Fallback story text when Gemini API call fails or key is unconfigured."""
    lines = []
    lines.append(f"=== {character_name}'s Adventure in {setting} ===\n")
    for panel in outline:
        num = panel.get("panel_number", 1)
        title = panel.get("title", f"Panel {num}")
        desc = panel.get("scene_description", "")
        lines.append(f"--- PANEL {num}: {title.upper()} ---")
        lines.append(f"[NARRATION]: Underneath the quiet hum of {setting}, destiny stirred.")
        lines.append(f"{desc}")
        lines.append(f'"{character_name}": "We must press on. There is no turning back now!"')
        lines.append(f"[CAPTION]: The tension hung in the air, thick and unpredictable.\n")
    return "\n".join(lines)


def generate_story(outline: list[dict], character_name: str, setting: str, tone: str) -> str:
    """
    Uses Gemini Pro (gemini-2.5-pro) to expand the outline into full comic narration + character dialogue for every panel.
    Returns one formatted text block covering all panels.
    """
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    print(f"\n[gemini_pro] >>> GEMINI_API_KEY loaded: '{api_key[:6]}...' (length: {len(api_key)})")

    if not api_key or api_key == "your_gemini_api_key_here":
        print("[gemini_pro] WARNING: GEMINI_API_KEY is not configured or placeholder. Returning mock story.")
        return _generate_mock_story(outline, character_name, setting, tone)

    try:
        genai.configure(api_key=api_key)

        outline_summary = ""
        for p in outline:
            num = p.get("panel_number")
            title = p.get("title")
            desc = p.get("scene_description")
            outline_summary += f"Panel {num}: {title} - {desc}\n"

        prompt = f"""
You are an award-winning comic book writer.
Expand the following 5-panel comic strip outline into full comic narration, sound effects (SFX), and character dialogue for every panel.

Story Details:
- Main Character: {character_name}
- Setting: {setting}
- Tone: {tone}

Outline:
{outline_summary}

Requirements:
- Structure the response clearly with headings for each panel: "--- PANEL 1: [Title] ---", "--- PANEL 2: [Title] ---", etc.
- In each panel, provide:
  - [CAPTION / NARRATION]: Atmosphere, internal thoughts, or narrative voice.
  - Character Dialogue: Clearly label character speech, e.g., {character_name}: "..."
  - Optional [SFX]: Dramatic sound effects if fitting (e.g. *CRACKLE*, *WHOOSH*).
- Maintain the requested {tone} tone consistently throughout.
- Keep each panel punchy and concise (2-4 lines of dialogue/narration) so the story moves briskly across all 5 panels.
- Return the full script as one formatted text block covering all 5 panels.
"""

        models_to_try = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"]
        response = None
        last_err = None

        for model_name in models_to_try:
            try:
                print(f"[gemini_pro] Initiating API call to Gemini ('{model_name}')...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.75, "max_output_tokens": 4096}
                )
                print(f"[gemini_pro] SUCCESS with model '{model_name}'!")
                break
            except Exception as pro_err:
                print(f"[gemini_pro] '{model_name}' failed: {pro_err}. Trying next...")
                last_err = pro_err

        if response is None:
            raise last_err

        story_text = response.text.strip() if hasattr(response, "text") and response.text else ""
        if not story_text:
            raise ValueError("Empty story response received from Gemini.")

        print(f"[gemini_pro] SUCCESS: Gemini story generation succeeded! Text length: {len(story_text)}")
        return story_text

    except Exception as e:
        status_code = getattr(e, "code", getattr(e, "status_code", "N/A"))
        print(f"\n========================================================")
        print(f"[gemini_pro] !!! FULL EXCEPTION IN generate_story !!!")
        print(f"Exception Type : {type(e).__name__}")
        print(f"Status Code    : {status_code}")
        print(f"Exception Message: {str(e)}")
        print(f"--- Full Traceback ---")
        traceback.print_exc()
        print(f"========================================================\n")
        print("[gemini_pro] Triggering fallback story due to the exception above.")
        return _generate_mock_story(outline, character_name, setting, tone)
