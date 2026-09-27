# ComicCraft

ComicCraft is an AI-powered comic generator that creates comic book panels and full comic strips using Google Gemini and image generation models.

## Features
- Generate comic panels from text prompts
- AI-powered story and dialogue generation (Gemini Flash / Pro)
- Automatic panel layout building
- Export finished comics as PDF

## Tech Stack
- Python (Flask/backend)
- Gemini API for text generation
- Image generation model for panel art

## Setup
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Add your API keys in a `.env` file (see `.gitignore` — this file is not included in the repo for security)
4. Run the app: `python app/main.py`

## Note
API keys and generated images/PDFs are excluded from this repository via `.gitignore`.
