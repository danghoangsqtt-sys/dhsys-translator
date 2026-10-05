from __future__ import annotations

import argparse
import hashlib
import json
import os
import wave
from pathlib import Path
from urllib.parse import urlparse

from videotrans.configure.config import ROOT_DIR, params
from videotrans.tts import EDGE_TTS, OMNIVOICE_TTS, OPENAI_TTS, run as run_tts
from videotrans.tts.pronunciation import BENCHMARK_FIXTURES, prepare_tts_text


TARGET_SECONDS = (1.5, 1.5, 2.0, 2.0, 2.0, 2.0, 2.5, 2.0, 2.0, 4.0, 3.0, 3.0)
PROVIDERS = {"edge", "vieneu", "omnivoice"}


def _slug(index: int, text: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    safe = "-".join(part for part in safe.split("-") if part)[:40]
    return f"{index:02d}-{safe or 'fixture'}"


def _wav_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
    return round(frames / rate, 3) if rate else 0.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_loopback_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def _queue_for(output_dir: Path, role: str) -> list[dict]:
    queue: list[dict] = []
    for index, (text, target_seconds) in enumerate(zip(BENCHMARK_FIXTURES, TARGET_SECONDS), start=1):
        queue.append({
            "text": text,
            "tts_text": prepare_tts_text(text, language="vi"),
            "role": role,
            "filename": str(output_dir / f"{_slug(index, text)}.wav"),
            "rate": "+0%",
            "volume": "+0%",
            "pitch": "+0Hz",
            "target_seconds": target_seconds,
        })
    return queue


def _result_from_queue(provider: str, queue: list[dict]) -> dict:
    audio = []
    ratios = []
    for index, item in enumerate(queue, start=1):
        path = Path(item["filename"])
        if not path.is_file():
            continue
        actual = _wav_duration_seconds(path)
        target = float(item["target_seconds"])
        ratio = round(actual / target, 3) if target else None
        if ratio is not None:
            ratios.append(ratio)
        audio.append({
            "fixture": BENCHMARK_FIXTURES[index - 1],
            "audio_file": path.name,
            "sha256": _sha256(path),
            "target_duration_seconds": target,
            "actual_duration_seconds": actual,
            "duration_ratio": ratio,
        })

    status = "pass" if len(audio) == len(queue) else "failed"
    within_20 = sum(0.8 <= ratio <= 1.2 for ratio in ratios)
    return {
        "provider": provider,
        "status": status,
        "generated_audio_count": len(audio),
        "expected_audio_count": len(queue),
        "pronunciation_accuracy": "pending_human_review",
        "naturalness": "pending_human_review",
        "voice_continuity": "pending_human_review",
        "duration_alignment": {
            "within_20_percent_count": within_20,
            "fixture_count": len(ratios),
            "mean_duration_ratio": round(sum(ratios) / len(ratios), 3) if ratios else None,
        },
        "audio": audio,
        "quality_claim": "No universal quality claim; listening review is required.",
    }


def _skip(provider: str, reason: str) -> dict:
    return {
        "provider": provider,
        "status": "skipped",
        "reason": reason,
        "pronunciation_accuracy": "not_scored",
        "naturalness": "not_scored",
        "voice_continuity": "not_scored",
        "duration_alignment": "not_scored",
        "quality_claim": "No universal quality claim; provider was not benchmarked.",
    }


def _failed(provider: str, error: Exception) -> dict:
    return {
        "provider": provider,
        "status": "failed",
        "reason": "provider_execution_failed",
        "error_type": type(error).__name__,
        "pronunciation_accuracy": "not_scored",
        "naturalness": "not_scored",
        "voice_continuity": "not_scored",
        "duration_alignment": "not_scored",
        "quality_claim": "No universal quality claim; provider execution failed.",
    }


def _exit_code(results: list[dict]) -> int:
    return 0 if results and all(item["status"] == "pass" for item in results) else 2


def _run_provider(provider: str, output_dir: Path, args: argparse.Namespace) -> dict:
    if provider == "edge":
        queue = _queue_for(output_dir, args.edge_voice)
        tts_type = EDGE_TTS
        is_cuda = False
    elif provider == "omnivoice":
        model = Path(ROOT_DIR) / "models" / "models--k2-fsa--OmniVoice" / "model.safetensors"
        if not model.is_file():
            return _skip(provider, "omnivoice_model_not_installed")
        queue = _queue_for(output_dir, "default")
        tts_type = OMNIVOICE_TTS
        is_cuda = args.cuda
    else:
        if not args.vieneu_model:
            return _skip(provider, "vieneu_model_not_configured")
        if not _is_loopback_url(args.vieneu_url):
            return _skip(provider, "vieneu_url_must_be_loopback")
        queue = _queue_for(output_dir, args.vieneu_voice)
        tts_type = OPENAI_TTS
        is_cuda = False

    output_dir.mkdir(parents=True, exist_ok=True)
    previous_openai = {}
    if provider == "vieneu":
        for key in ("openaitts_api", "openaitts_key", "openaitts_model", "openaitts_instructions"):
            previous_openai[key] = params.get(key)
        params["openaitts_api"] = args.vieneu_url
        params["openaitts_key"] = os.environ.get(args.vieneu_key_env, "local-pilot")
        params["openaitts_model"] = args.vieneu_model
        params["openaitts_instructions"] = ""

    try:
        run_tts(
            queue_tts=queue,
            language="vi",
            uuid=f"task-4.16-{provider}",
            tts_type=tts_type,
            is_cuda=is_cuda,
        )
        return _result_from_queue(provider, queue)
    except Exception as error:
        return _failed(provider, error)
    finally:
        if provider == "vieneu":
            for key, value in previous_openai.items():
                params[key] = value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Task 4.16 TTS pronunciation benchmark. Output contains no API key or absolute path.",
    )
    parser.add_argument(
        "--providers",
        default="edge,vieneu,omnivoice",
        help="Comma-separated: edge,vieneu,omnivoice",
    )
    parser.add_argument("--output-dir", default="tmp/task-4.16-tts-benchmark")
    parser.add_argument("--edge-voice", default="vi-VN-HoaiMyNeural")
    parser.add_argument("--vieneu-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--vieneu-model", default=os.environ.get("PYVIDEOTRANS_VIENEU_MODEL", ""))
    parser.add_argument("--vieneu-voice", default=os.environ.get("PYVIDEOTRANS_VIENEU_VOICE", "default"))
    parser.add_argument("--vieneu-key-env", default="PYVIDEOTRANS_VIENEU_KEY")
    parser.add_argument("--cuda", action="store_true", help="Use CUDA for OmniVoice when installed.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir)
    if output_dir.is_absolute():
        raise SystemExit("--output-dir must be repository-relative so reports/logs do not expose a local path")

    providers = [item.strip().lower() for item in args.providers.split(",") if item.strip()]
    unknown = sorted(set(providers) - PROVIDERS)
    if unknown:
        raise SystemExit(f"Unknown provider(s): {', '.join(unknown)}")

    results = []
    for provider in providers:
        results.append(_run_provider(provider, output_dir / provider, args))

    report = {
        "task": "4.16",
        "language": "vi",
        "fixture_count": len(BENCHMARK_FIXTURES),
        "fixtures": list(BENCHMARK_FIXTURES),
        "results": results,
        "notes": [
            "Pronunciation accuracy, naturalness and voice continuity require human listening review.",
            "Duration alignment compares generated WAV duration with the fixed benchmark time budget.",
            "No API key, reference-audio path or absolute local path is stored in this report.",
            "This benchmark does not establish universal provider quality.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "benchmark-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    return _exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
