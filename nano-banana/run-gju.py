#!/usr/bin/env python3
"""Run the GJU-themed prompt set into outputs/gju/."""
from pathlib import Path
import yaml
from generate import generate
from google import genai

client = genai.Client()
out_dir = Path("outputs/gju")
out_dir.mkdir(parents=True, exist_ok=True)

prompts = yaml.safe_load(Path("gju-prompts.yaml").read_text())
for entry in prompts:
    fname = entry["filename"]
    print(f"… {fname}  ({entry['role']})")
    data = generate(client, entry["prompt"], None)
    (out_dir / fname).write_bytes(data)
    print(f"✓ {out_dir / fname}")
print(f"done: {len(prompts)} image(s)")
