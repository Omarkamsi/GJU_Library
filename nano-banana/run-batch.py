#!/usr/bin/env python3
"""Read image-prompts.yaml and generate every image into outputs/.

Run after billing is enabled:
  GEMINI_API_KEY=... .venv/bin/python run-batch.py
"""
from pathlib import Path
import yaml
from generate import generate
from google import genai

client = genai.Client()
out_dir = Path("outputs")
out_dir.mkdir(exist_ok=True)

prompts = yaml.safe_load(Path("image-prompts.yaml").read_text())
for entry in prompts:
    fname = entry["filename"]
    print(f"… {fname}  ({entry['role']})")
    data = generate(client, entry["prompt"], None)
    (out_dir / fname).write_bytes(data)
    print(f"✓ {out_dir / fname}")
print(f"done: {len(prompts)} image(s)")
