#!/usr/bin/env python3
# Gemini (flagship) headless caller — the 4th teacher. Key comes from env (GEMINI_API_KEY) only; never hard-code.
# Usage: GEMINI_API_KEY=... python gemini_cli.py "<PROMPT>"  (or via stdin)
import os, sys

def main():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        sys.stderr.write("no GEMINI_API_KEY\n"); sys.exit(2)
    prompt = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
    try:
        from google import genai
        client = genai.Client(api_key=key)
        r = client.models.generate_content(model=model, contents=prompt)
        print(r.text or "")
    except Exception as e:
        sys.stderr.write(f"gemini err: {str(e)[:200]}\n"); sys.exit(1)

if __name__ == "__main__":
    main()
