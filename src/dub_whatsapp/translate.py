#!/usr/bin/env python3
import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def write_text(path: str, value: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(value.strip() + "\n")


def ollama_generate(model: str, prompt: str) -> str:
    data = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("response", "").strip()


def ensure_ollama_running() -> None:
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3).close()
        return
    except Exception:
        pass

    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        time.sleep(0.5)
        try:
            urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3).close()
            return
        except Exception:
            continue
    raise RuntimeError("Ollama server is not responding")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--input-language", default="Spanish")
    parser.add_argument("--output-language", default="English")
    args = parser.parse_args()

    source_text = read_text(args.input)
    if not source_text:
        raise SystemExit("input transcript is empty")

    ensure_ollama_running()
    prompt = f"""Translate this {args.input_language} transcript into natural spoken {args.output_language}.

Rules:
- Return only the {args.output_language} translation.
- Preserve meaning, tone, names, numbers, and pauses where useful.
- Do not add explanations, labels, Markdown, or quotation marks.

{args.input_language} transcript:
{source_text}
"""
    try:
        translation = ollama_generate(args.model, prompt)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Ollama request failed: {exc.code} {body}") from exc

    if not translation:
        raise SystemExit("Ollama returned an empty translation")
    write_text(args.output, translation)


if __name__ == "__main__":
    main()
