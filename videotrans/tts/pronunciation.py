from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping


TTS_GLOSSARY_FILENAME = "tts-glossary.txt"

# Conservative Vietnamese-first defaults for common technical names.  This is
# intentionally small: project entries can override these without changing the
# subtitle text saved or displayed to the user.
DEFAULT_VI_TECH_GLOSSARY: dict[str, str] = {
    "OpenRouter": "Ô-pần Rau-tơ",
    "ChatGPT": "Chát Gi Pi Ti",
    "NVIDIA": "En Vi Đi A",
    "GitHub": "Ghít Hắp",
    "Docker": "Đóc-cơ",
    "Python": "Pai-thần",
    "Gemini": "Gemini",
    "API": "ây pi ai",
    "AI": "ây ai",
}

BENCHMARK_FIXTURES: tuple[str, ...] = (
    "AI",
    "API",
    "ChatGPT",
    "GitHub",
    "Docker",
    "Python",
    "OpenRouter",
    "Gemini",
    "NVIDIA",
    "https://github.com/openai",
    "support@example.com",
    "version 3.12.14",
)


def parse_tts_glossary(content: str) -> dict[str, str]:
    """Parse ``term=spoken form`` lines; later duplicates win."""
    parsed: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        source, spoken = (part.strip() for part in line.split("=", 1))
        if source and spoken:
            parsed[source] = spoken
    return parsed


def load_project_tts_glossary(project_dir: str | Path | None) -> dict[str, str]:
    """Load an optional project-local glossary without creating or logging it."""
    if not project_dir:
        return {}
    path = Path(project_dir) / TTS_GLOSSARY_FILENAME
    if not path.is_file():
        return {}
    return parse_tts_glossary(path.read_text(encoding="utf-8-sig", errors="ignore"))


def _merge_glossaries(*glossaries: Mapping[str, str]) -> list[tuple[str, str]]:
    # Case-insensitive keys give project/user overrides deterministic precedence.
    merged: dict[str, tuple[str, str]] = {}
    for glossary in glossaries:
        for source, spoken in glossary.items():
            source = str(source).strip()
            spoken = str(spoken).strip()
            if source and spoken:
                merged[source.casefold()] = (source, spoken)
    return sorted(merged.values(), key=lambda item: (-len(item[0]), item[0].casefold(), item[0]))


def prepare_tts_text(
    text: str,
    *,
    language: str = "",
    project_dir: str | Path | None = None,
    glossary: Mapping[str, str] | None = None,
) -> str:
    """Return transient speech text while leaving the supplied subtitle untouched.

    The pronunciation layer is Vietnamese-only for this pilot.  Precedence is
    explicit glossary > project ``tts-glossary.txt`` > built-in defaults, and
    longest terms are matched first so nested names remain deterministic.
    """
    if not text or not str(language).lower().startswith("vi"):
        return text

    entries = _merge_glossaries(
        DEFAULT_VI_TECH_GLOSSARY,
        load_project_tts_glossary(project_dir),
        glossary or {},
    )
    if not entries:
        return text

    replacement_by_key = {source.casefold(): spoken for source, spoken in entries}
    alternatives = "|".join(re.escape(source) for source, _ in entries)
    pattern = re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", flags=re.IGNORECASE)
    return pattern.sub(lambda match: replacement_by_key[match.group(0).casefold()], text)
