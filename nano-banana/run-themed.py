#!/usr/bin/env python3
"""Generate the GJU-themed image set, conditioning each call on the actual
GJU logo so the model copies its real palette and geometry."""
from pathlib import Path
import yaml
from generate import generate
from google import genai

LOGO = Path("/root/gju logo.png")

client = genai.Client()
out_dir = Path("outputs")
out_dir.mkdir(parents=True, exist_ok=True)

prompts = yaml.safe_load(Path("themed-prompts.yaml").read_text())
for entry in prompts:
    fname = entry["filename"]
    print(f"… {fname}  ({entry['role']})")
    data = generate(client, entry["prompt"], LOGO)
    (out_dir / fname).write_bytes(data)
    print(f"✓ {out_dir / fname}")
print(f"done: {len(prompts)} image(s)")
