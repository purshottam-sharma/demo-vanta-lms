#!/usr/bin/env python3
"""
Thin wrapper around the Google Gemini API for vision + text tasks.

Used by Design Agent (Figma frame analysis) and Visual Diff Agent (diff PNG reading).
All code-generation and tool-use tasks remain with Claude — Gemini is used exclusively
for image understanding steps where it produces better results.

Usage:
    # Text only
    python3 agents/shared/gemini.py --prompt "Describe this layout"

    # Vision (one or more images)
    python3 agents/shared/gemini.py \
      --prompt "What's different in the red regions?" \
      --image /tmp/diff-86d2c0nmj.png

    # Multiple images
    python3 agents/shared/gemini.py \
      --prompt "Compare these two screenshots" \
      --image /tmp/figma.png \
      --image /tmp/rendered.png

    # Read prompt from file (useful for long prompts)
    python3 agents/shared/gemini.py \
      --prompt-file /tmp/vision-prompt.txt \
      --image /tmp/diff.png

    # Output JSON only (strip markdown fences if present)
    python3 agents/shared/gemini.py \
      --prompt "..." --image /tmp/diff.png --json

Requires in environment (or .env):
    GEMINI_API_KEY=...
    GEMINI_MODEL=gemini-2.5-pro-preview   (optional, this is the default)

Output:
    Prints Gemini's response text to stdout.
    Exits with code 1 on error (error JSON written to stdout).
"""

import sys
import os
import json
import base64
import argparse
import urllib.request
import urllib.error


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-2.5-pro-preview"


def load_env() -> dict:
    """Load GEMINI_API_KEY and GEMINI_MODEL from environment or project .env."""
    env = {}
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env[key.strip()] = val.strip().strip('"').strip("'")
    return {
        "api_key": os.environ.get("GEMINI_API_KEY") or env.get("GEMINI_API_KEY"),
        "model": os.environ.get("GEMINI_MODEL") or env.get("GEMINI_MODEL") or DEFAULT_MODEL,
    }


def image_to_part(image_path: str) -> dict:
    """Load an image file and return a Gemini inline_data part."""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/png")

    return {"inline_data": {"mime_type": mime, "data": data}}


def call_gemini(
    prompt: str,
    image_paths: list[str] | None = None,
    temperature: float = 0.2,
) -> str:
    """
    Call the Gemini API with text + optional images.

    Returns the response text.
    Raises RuntimeError on API error.
    """
    cfg = load_env()
    if not cfg["api_key"]:
        raise ValueError(
            "GEMINI_API_KEY not set. Add it to .env or set the environment variable."
        )

    model = cfg["model"]
    api_key = cfg["api_key"]

    # Build parts list: images first (better grounding), then prompt text
    parts = []
    for path in (image_paths or []):
        parts.append(image_to_part(path))
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 8192,
        },
    }

    url = f"{GEMINI_API_BASE}/{model}:generateContent?key={api_key}"
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini API error {e.code}: {error_body}")

    # Extract text from response
    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates in Gemini response: {result}")

    content = candidates[0].get("content", {})
    parts_out = content.get("parts", [])
    text = "".join(p.get("text", "") for p in parts_out)

    if not text:
        finish = candidates[0].get("finishReason", "unknown")
        raise RuntimeError(f"Empty Gemini response (finishReason={finish}): {result}")

    return text


def strip_json_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()
    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Call Gemini API for vision/text tasks")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt", help="Prompt text")
    group.add_argument("--prompt-file", help="Read prompt from this file")
    parser.add_argument("--image", action="append", dest="images", default=[],
                        help="Image path(s) to include (can be specified multiple times)")
    parser.add_argument("--json", action="store_true", dest="json_mode",
                        help="Strip markdown fences and validate JSON output")
    parser.add_argument("--temperature", type=float, default=0.2,
                        help="Generation temperature (default: 0.2)")
    args = parser.parse_args()

    if args.prompt_file:
        with open(args.prompt_file) as f:
            prompt = f.read()
    else:
        prompt = args.prompt

    try:
        response = call_gemini(prompt, args.images, args.temperature)

        if args.json_mode:
            response = strip_json_fences(response)
            # Validate it's real JSON
            try:
                json.loads(response)
            except json.JSONDecodeError as e:
                print(json.dumps({"error": f"Gemini returned invalid JSON: {e}", "raw": response}))
                sys.exit(1)

        print(response)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
