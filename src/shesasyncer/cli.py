"""Command-line interface for real ShesASyncer alignment runs."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from .engines.ctc import CtcSingingEngine
from .engines.onnx_ctc import OnnxCtcRunner
from .lyrics.g2p import EspeakG2P

MODEL_URL = "https://huggingface.co/sadda-speech/wav2vec2-espeak-ctc/resolve/main/model.onnx"
VOCAB_URL = "https://huggingface.co/sadda-speech/wav2vec2-espeak-ctc/resolve/main/vocab.json"


def _read_lyrics(path: Path) -> list[str]:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.strip()
        if not text:
            continue
        while text.startswith("[") and "]" in text[:12]:
            text = text[text.index("]") + 1 :].strip()
        if text:
            lines.append(text)
    return lines


def _ffmpeg_audio(path: Path) -> tuple[str, tempfile.TemporaryDirectory[str] | None]:
    if path.suffix.lower() == ".wav":
        return str(path), None
    if not shutil.which("ffmpeg"):
        raise RuntimeError("Non-WAV audio requires ffmpeg. Install it or provide a 16-bit PCM WAV file.")
    temp = tempfile.TemporaryDirectory(prefix="shesasyncer-")
    target = Path(temp.name) / "audio.wav"
    command = ["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", str(target)]
    subprocess.run(command, check=True)
    return str(target), temp


def _write_lrc(lines, path: Path) -> None:
    def stamp(seconds):
        minutes = int(seconds // 60)
        hundredths = int(round((seconds - minutes * 60) * 100))
        if hundredths >= 100:
            minutes += 1
            hundredths = 0
        return f"{minutes:02d}:{hundredths / 100:05.2f}"

    path.write_text(
        "\n".join(
            f"[{stamp(item['start'])}] {item['text']}" if item["start"] is not None else f"[??:??.??] {item['text']}"
            for item in lines
        ) + "\n",
        encoding="utf-8",
    )


def _write_html(lines, confidence: float, path: Path) -> None:
    rows = []
    for item in lines:
        start = "—" if item["start"] is None else f"{item['start']:.3f}s"
        end = "—" if item["end"] is None else f"{item['end']:.3f}s"
        item_confidence = f"{item['confidence']:.3f}"
        rows.append(
            f"<tr><td>{item['index']}</td><td>{start}</td><td>{end}</td><td>{item_confidence}</td>"
            f"<td>{_escape(item['source'])}</td><td>{_escape(item['text'])}</td></tr>"
        )
    html = """<!doctype html><meta charset='utf-8'><title>ShesASyncer alignment</title>
<style>body{font:15px system-ui;margin:32px;max-width:1200px}table{border-collapse:collapse;width:100%}th,td{padding:8px;border-bottom:1px solid #ddd;text-align:left}th{position:sticky;top:0;background:#fff}</style>
<h1>ShesASyncer alignment</h1>
<p>Overall confidence: <b>{confidence:.3f}</b></p>
<table><thead><tr><th>#</th><th>Start</th><th>End</th><th>Confidence</th><th>Source</th><th>Trusted lyric</th></tr></thead><tbody>{rows}</tbody></table>
""".format(confidence=confidence, rows="".join(rows))
    path.write_text(html, encoding="utf-8")


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _download(url: str, target: Path, *, attempts: int = 3) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    for attempt in range(1, attempts + 1):
        existing = partial.stat().st_size if partial.exists() else 0
        headers = {"Range": f"bytes={existing}-"} if existing else {}
        request = urllib.request.Request(url, headers=headers)
        try:
            print(f"Downloading {target.name}...", file=sys.stderr)
            with urllib.request.urlopen(request, timeout=60) as response:
                status = getattr(response, "status", 200)
                if existing and status != 206:
                    existing = 0
                    partial.unlink(missing_ok=True)
                mode = "ab" if existing and status == 206 else "wb"
                with partial.open(mode) as handle:
                    shutil.copyfileobj(response, handle)
            partial.replace(target)
            return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == attempts:
                raise RuntimeError(f"Download failed after {attempts} attempts: {url}") from exc
            print(f"Download attempt {attempt} failed; retrying...", file=sys.stderr)


def setup_model(directory: Path) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    model = directory / "model.onnx"
    vocab = directory / "vocab.json"
    if not model.exists():
        _download(MODEL_URL, model)
    if not vocab.exists():
        _download(VOCAB_URL, vocab)
    print(f"Model: {model}")
    print(f"Vocabulary: {vocab}")
    return 0


def _segments_payload(segments) -> tuple[list[dict], float]:
    lines = []
    for index, segment in enumerate(segments, start=1):
        lines.append({
            "index": index,
            "start": segment.start,
            "end": segment.end,
            "confidence": segment.confidence,
            "source": "ctc",
            "text": segment.text,
            "phonemes": list(segment.phonemes),
        })
    confidence = sum(item["confidence"] for item in lines) / len(lines) if lines else 0.0
    return lines, confidence


def align(args: argparse.Namespace) -> int:
    audio = Path(args.audio).expanduser().resolve()
    lyrics = Path(args.lyrics).expanduser().resolve()
    if not audio.exists():
        raise FileNotFoundError(audio)
    if not lyrics.exists():
        raise FileNotFoundError(lyrics)

    model = Path(args.model).expanduser().resolve()
    vocab = Path(args.vocab).expanduser().resolve()
    if not model.exists() or not vocab.exists():
        raise FileNotFoundError("Model assets not found. Run `python -m shesasyncer model setup` first.")

    lyric_lines = _read_lyrics(lyrics)
    if not lyric_lines:
        raise ValueError("No lyric lines found.")

    audio_path, temp = _ffmpeg_audio(audio)
    try:
        engine = CtcSingingEngine(
            EspeakG2P(),
            OnnxCtcRunner(str(model), str(vocab), blank_token="<pad>"),
            blank_token="<pad>",
        )
        segments = engine.align(audio_path, lyric_lines, args.language)
        lines, confidence = _segments_payload(segments)
        payload = {
            "engine": engine.name,
            "audio": str(audio),
            "lyrics": str(lyrics),
            "confidence": confidence,
            "warnings": [] if len(lines) == len(lyric_lines) else ["Some lyric lines could not be aligned."],
            "lines": lines,
        }
        output = Path(args.output).expanduser().resolve() if args.output else audio.with_suffix(".shesasyncer.json")
        output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_lrc(lines, output.with_suffix(".lrc"))
        _write_html(lines, confidence, output.with_suffix(".html"))
        print(f"JSON: {output}")
        print(f"LRC:  {output.with_suffix('.lrc')}")
        print(f"HTML: {output.with_suffix('.html')}")
        print(f"Confidence: {confidence:.3f}")
        return 0
    finally:
        if temp is not None:
            temp.cleanup()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shesasyncer", description="Align trusted lyrics to singing audio.")
    sub = parser.add_subparsers(dest="command", required=True)

    model_parser = sub.add_parser("model", help="Manage the reference CTC model")
    model_sub = model_parser.add_subparsers(dest="model_command", required=True)
    setup_parser = model_sub.add_parser("setup", help="Download the Apache-2.0 reference ONNX model and vocabulary")
    setup_parser.add_argument("--directory", default=os.path.expanduser("~/.cache/shesasyncer/model"))

    align_parser = sub.add_parser("align", help="Run native CTC singing alignment")
    align_parser.add_argument("audio")
    align_parser.add_argument("lyrics")
    align_parser.add_argument("--model", default=os.path.expanduser("~/.cache/shesasyncer/model/model.onnx"))
    align_parser.add_argument("--vocab", default=os.path.expanduser("~/.cache/shesasyncer/model/vocab.json"))
    align_parser.add_argument("--language", default=None)
    align_parser.add_argument("--output", default=None)

    args = parser.parse_args(argv)
    if args.command == "model":
        return setup_model(Path(args.directory).expanduser())
    if args.command == "align":
        return align(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
