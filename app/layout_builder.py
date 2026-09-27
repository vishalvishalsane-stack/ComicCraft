import re
import logging

logger = logging.getLogger(__name__)


def _extract_panel_texts(story_text: str, total_panels: int = 5) -> dict[int, str]:
    """
    Parses a multi-panel story script text block and extracts the text
    belonging to each panel number (1 to total_panels).
    """
    panel_texts = {}
    
    # Split text by panel headers like "--- PANEL 1: ... ---", "### Panel 1:", "**PANEL 1:**", etc.
    pattern = r"(?:^|\n)\s*[\#\*\-=_ \t]*(?:PANEL|Panel)\s*(\d+)[:\s\-\w\*\#=_]*\n?"
    parts = re.split(pattern, story_text)
    
    if len(parts) > 1:
        # parts[0] is preamble before panel 1
        # followed by (panel_num, panel_body) pairs
        for i in range(1, len(parts), 2):
            try:
                p_num = int(parts[i])
                p_body = parts[i + 1].strip() if (i + 1) < len(parts) else ""
                panel_texts[p_num] = p_body
            except (ValueError, IndexError):
                continue

    return panel_texts


def build_comic_layout(outline: list[dict], story_text: str, image_paths: list[str]) -> list[dict]:
    """
    Merges generated images with the story text per panel.
    Returns a list of dicts:
      - panel_number: int
      - title: str
      - image_path: str
      - scene_description: str
      - text: str (narration / dialogue)
      - image_prompt: str
    """
    extracted_texts = _extract_panel_texts(story_text, total_panels=len(outline))
    layout = []

    for i, panel in enumerate(outline):
        p_num = panel.get("panel_number", i + 1)
        title = panel.get("title", f"Panel {p_num}")
        scene_desc = panel.get("scene_description", "")
        img_prompt = panel.get("image_prompt", "")
        img_path = image_paths[i] if i < len(image_paths) else "/static/panels/default.png"

        # Determine the dialogue/narration text for this panel
        panel_text = extracted_texts.get(p_num)
        if not panel_text:
            # Fallback if parsing didn't find specific panel block
            panel_text = f"[SCENE]: {scene_desc}\n[NARRATION]: The journey continues as destiny unfolds."

        layout.append({
            "panel_number": p_num,
            "title": title,
            "image_path": img_path,
            "scene_description": scene_desc,
            "text": panel_text,
            "image_prompt": img_prompt,
        })

    return layout
