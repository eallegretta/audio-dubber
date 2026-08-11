#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return re.sub(r"\s+", " ", f.read()).strip()


def split_text(text: str, max_chars: int = 420) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for part in parts:
        if not part:
            continue
        candidate = f"{current} {part}".strip()
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = part
    if current:
        chunks.append(current)
    return chunks or [text]


def as_numpy(audio) -> np.ndarray:
    if hasattr(audio, "tolist"):
        audio = audio.tolist()
    arr = np.asarray(audio, dtype=np.float32)
    if arr.ndim > 1:
        arr = arr.reshape(-1)
    return arr


def get_sample_rate(model, result) -> int:
    for obj in (result, model):
        for attr in ("sample_rate", "sampling_rate", "sr"):
            value = getattr(obj, attr, None)
            if isinstance(value, int) and value > 0:
                return value
    return 24000


def status(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--ref-audio", required=True)
    parser.add_argument("--ref-text", required=True)
    parser.add_argument("--language", default="English")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    target_text = read_text(args.text)
    ref_text = read_text(args.ref_text)
    if not target_text:
        raise SystemExit("Target text is empty")
    if not ref_text:
        raise SystemExit("Reference transcript is empty")

    status(f"Loading TTS model: {args.model}")
    model = load_model(args.model)
    chunks = split_text(target_text)
    status(f"Generating {len(chunks)} audio chunk(s)")
    audio_parts: list[np.ndarray] = []
    sample_rate = 24000

    for index, chunk in enumerate(chunks, start=1):
        status(f"Generating chunk {index}/{len(chunks)}")
        try:
            results = list(
                model.generate(
                    text=chunk,
                    ref_audio=args.ref_audio,
                    ref_text=ref_text,
                    language=args.language,
                )
            )
        except TypeError:
            results = list(
                model.generate(
                    text=chunk,
                    ref_audio=args.ref_audio,
                    ref_text=ref_text,
                )
            )
        if not results:
            raise SystemExit("Qwen3-TTS returned no audio")
        for result in results:
            sample_rate = get_sample_rate(model, result)
            audio_parts.append(as_numpy(result.audio))
            audio_parts.append(np.zeros(int(sample_rate * 0.18), dtype=np.float32))

    audio = np.concatenate(audio_parts) if audio_parts else np.zeros(1, dtype=np.float32)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 1.0:
        audio = audio / peak

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    status(f"Writing temporary WAV: {output}")
    sf.write(str(output), audio, sample_rate)


if __name__ == "__main__":
    main()
