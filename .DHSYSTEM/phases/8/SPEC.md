# Phase 8 — Provider mặc định dùng được ở Việt Nam

Status: complete (2026-10-22). Request: [ENH-009](../../requests/ENH-009.md). Builds on Phase 7 / ENH-007. Product manifest remains 4.14.

## Goal

The default desktop provider lists show only services a Vietnamese user can reach without a China-hosted or less-common international account. Everything else stays installed, configurable and selectable through one Advanced switch.

## Default visibility contract

| Group | Translation | Recognition | TTS |
| --- | --- | --- | --- |
| Online, no key | Google, Microsoft | Google Speech | Edge-TTS, gTTS |
| API account (international) | ChatGPT/OpenAI, Gemini, OpenRouter | OpenAI API, Gemini, OpenRouter | OpenAI TTS, Gemini TTS, OpenRouter |
| Local model / local service | M2M100, Local LLM, LiteLLM, DeepLX, Libre | faster-whisper, OpenAI Whisper, Whisper.cpp, XXL, WhisperX API, Parakeet, Nemotron, Omnilingual, HuggingFace ASR, Whisper.NET | F5, OmniVoice, Piper, Chatterbox, Supertonic, GPT-SoVITS, Kokoro |
| Custom endpoint | TransAPI | STT API, Custom API | TTS API |

Moved to Advanced (hidden by default): DeepSeek, Azure GPT, DeepL, Deepgram, ElevenLabs (STT/TTS), Azure TTS, and every China-hosted cloud provider already outside the ENH-007 curated set.

## Compatibility contract

- Registries remain contiguous and unchanged: translation `0..28`, recognition `0..32`, TTS `0..37`.
- Hiding stays presentation-only; CLI, WebUI processing, credentials and persisted numeric indexes keep working.
- A saved hidden provider stays selected and visible, labelled "(ẩn)" / "(hidden)", until the user changes it.
- The existing `show_all_providers` key is reused; its action moves from the provider menu to Advanced settings.

## Task order

1. [8.1](tasks/8.1.md) — narrow the curated policy and move the show-all switch to Advanced.
2. [8.2](tasks/8.2.md) — find and close every surface that still lists hidden providers.
3. [8.3](tasks/8.3.md) — rebuild the frozen candidate and record acceptance.
