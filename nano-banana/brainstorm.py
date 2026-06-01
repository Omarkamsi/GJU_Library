#!/usr/bin/env python3
"""Ask Gemini text model to brainstorm image needs + prompts for the GJU Library AI."""
import os
from google import genai

client = genai.Client()

req = """You are an art director for a small in-house web app: the GJU Library AI Assistant.
It's a trilingual (EN/AR/DE) chatbot for the German Jordanian University library, plus a
landing page where students sign in and ask questions. Modest, academic, friendly tone —
not corporate. Cream/dark-green palette. No stock-photo people.

List the 5 most useful images the project would actually benefit from (e.g. logo, hero,
empty-state illustration, og-image for social previews, etc.). For each, output:
  - filename (kebab-case, .png)
  - role (one phrase, e.g. "homepage hero")
  - dimensions (e.g. 1200x630)
  - prompt: a single self-contained image-generation prompt I can feed verbatim to
    gemini-2.5-flash-image. Be visually specific (style, palette, composition). Do NOT
    include any text inside the image.

Output as valid YAML, no extra commentary."""

resp = client.models.generate_content(model="gemini-2.5-flash", contents=req)
print(resp.text)
