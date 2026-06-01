#!/usr/bin/env python3
"""Standalone Gemini 2.5 Flash Image (a.k.a. "nano-banana") CLI.

Usage:
  GEMINI_API_KEY=... python generate.py "a watercolor of the GJU library at sunset" -o out.png
  GEMINI_API_KEY=... python generate.py -p prompts.txt -d outputs/   # batch from a prompt file
  GEMINI_API_KEY=... python generate.py "make this poster" -i input.png -o edited.png   # image edit

Install once:
  pip install google-genai pillow
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO


MODEL = "gemini-2.5-flash-image"


def generate(client: genai.Client, prompt: str, input_path: Path | None) -> bytes:
    parts: list = [prompt]
    if input_path is not None:
        parts.append(Image.open(input_path))
    resp = client.models.generate_content(model=MODEL, contents=parts)
    for cand in resp.candidates or []:
        for part in cand.content.parts or []:
            if part.inline_data is not None:
                return part.inline_data.data
    raise RuntimeError("no image returned; response text: " + (resp.text or ""))


def slugify(s: str, n: int = 40) -> str:
    out = "".join(c if c.isalnum() else "-" for c in s.lower())[:n].strip("-")
    return out or "image"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", help="text prompt (or omit and use --prompts-file)")
    ap.add_argument("-o", "--out", help="output PNG path (single-prompt mode)")
    ap.add_argument("-d", "--out-dir", default="outputs", help="output dir (batch mode)")
    ap.add_argument("-p", "--prompts-file", help="file with one prompt per line")
    ap.add_argument("-i", "--input", help="input image (enables image-edit mode)")
    args = ap.parse_args()

    if "GEMINI_API_KEY" not in os.environ:
        print("error: set GEMINI_API_KEY in env", file=sys.stderr)
        return 2

    client = genai.Client()

    if args.prompts_file:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        prompts = [p.strip() for p in Path(args.prompts_file).read_text().splitlines() if p.strip()]
        for i, p in enumerate(prompts, 1):
            data = generate(client, p, Path(args.input) if args.input else None)
            path = out_dir / f"{i:02d}-{slugify(p)}.png"
            path.write_bytes(data)
            print(f"✓ {path}  ({p[:60]})")
        return 0

    if not args.prompt:
        ap.error("provide a prompt or --prompts-file")
    out_path = Path(args.out or f"{slugify(args.prompt)}.png")
    data = generate(client, args.prompt, Path(args.input) if args.input else None)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    print(f"✓ wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
