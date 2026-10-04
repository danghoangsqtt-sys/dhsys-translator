# Changelog

## Unreleased

Planned for patch 4.14.1: repair legacy configuration startup, data and secret handling, Docker/frozen runtime paths, process/network/download reliability, locale compatibility, and binding release tests. These audit fixes remain open until implemented and verified; current product version is 4.14. See `docs/BUGFIX-PLAN.md`.

- Locally verified: legacy `params.json` migration no longer crashes on missing/invalid fields; Docker build context excludes local configuration and credential files. Release and Git persistence gates remain open.
- Locally verified: startup/completion cache cleanup rejects outside and symlinked paths; CLI now reserves distinct output and cache directories for every run, preserving prior exports and concurrent results.
- In progress: Docker WebUI now receives explicit bind host/port and runtime credentials; frozen desktop paths separate bundled resources from writable user data. Container and extracted artifact smoke remain open.
- Locally verified: explicit CA bundles remain configured; GUI shutdown targets only app-owned FFmpeg descendants. A live process probe preserved an unrelated FFmpeg render.
- Locally verified: Hugging Face download callbacks no longer patch global functions; model cache/downloads validate size and SHA-256 before atomic replacement.
- Locally verified: persisted language codes select valid WebUI labels and voices; desktop short language flags take effect before configuration loads. CLI/Qt tests exercise actual actions and worker stages.
- Locally verified: Python 3.10–3.12 install locked core and `wetext` wheels and pass 540 tests each. Chatterbox/Perth commits and the FFmpeg archive checksum are pinned; a local FFmpeg media smoke passed.
- Locally verified: the Python 3.12 onedir Windows candidate starts headlessly with isolated user data; the workflow uses that runtime after a reproducible Python 3.10 PyInstaller stack overflow. Runner, Docker and packaged media gates remain open.

- Restored the Python 3.10 regression suite and aligned CLI version and install documentation with the project manifest.
- Removed execution of VibeVoice response text; added bounded segment validation.
- Restored HTTPS certificate verification for recognition, translation, TTS and downloads.
- Bound WebUI to loopback by default and required authentication for network and share modes.
- Preserved older output on reruns and limited cache cleanup to the managed temp directory.
