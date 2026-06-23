"""Server-side configuration (secrets and AI settings)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
SNAPFLOW_API_KEY = os.getenv("SNAPFLOW_API_KEY", "")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_REFERER = os.getenv("OPENROUTER_REFERER", "http://localhost:5000")

SYSTEM_PROMPT = """Analyze this screenshot. If it contains a date/time, return a calendar event.
If it contains an address, return a map link. If it contains text, return clean markdown.
If it contains code, return a code block.

Output must be valid JSON with exactly this shape:
{"type": "action_type", "data": "the_processed_content"}

Use these action_type values:
- "calendar" — data is JSON string with keys: title, start (ISO 8601), end (ISO 8601, optional), location (optional), description (optional)
- "map" — data is a full Google Maps URL for the address
- "markdown" — data is clean markdown text
- "code" — data is the code content (no markdown fences)

If nothing useful is detected, use type "error" and data with a short explanation."""
