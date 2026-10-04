# Changelog

## Unreleased

- The desktop workflow now numbers its five existing steps and separates the existing Start/Retry, task activity, and subtitle-preview areas for faster scanning. No processing controls or behavior changed.

- Workflow cards now show a localized ready, processing, attention, or complete state from existing task events. The new presentation bridge does not alter queues, media processing, saved settings, output paths, dialogs, or CLI behavior.

- Light workspace now groups the original controls into five labeled workflow sections while preserving every widget/action handler. Local candidate `dist/sp/sp.exe` SHA-256 `6b5d70b334489d976a5c96f54cf6d8a331cc523f9d80bd2a228d7a9faf1c816e` passes frozen resource and UI probes with all five sections.

- Local Windows light-interface candidate rebuilt from tracked `sp.spec`; `dist/sp/sp.exe` SHA-256 `8c3396a06c41fee7f59effb22a03a0175e1db38be3c4345d6cd3f3a8236a7e3d`. Frozen resource/provider/dialog/CLI/SRT/MP4 smoke, WorkspaceShell/UI smoke, 5 sidebar routes and 71 dynamic-menu routes pass. This is local verification, not release 4.14.1.

- Desktop candidate ngày 2026-10-04: thêm `vi_VN` cho giao diện, bộ chọn ngôn ngữ trên trang chủ, splash Qt và trang chủ “Xưởng Video”, cùng lối tắt đến không gian làm việc và bốn công cụ. Bỏ liên kết quảng bá dự án cũ khỏi các bề mặt mở đầu và menu trợ giúp; giữ thông tin GPL trong About. Kiểm tra nguồn đạt 546 test; gói Windows mới đạt smoke giao diện, 5/5 sidebar, 71/71 menu động, CLI/SRT/media mẫu và khởi động GUI. Tên hiển thị và bản dịch dài cần người dùng rà soát; đây chưa phải phát hành 4.14.1.

Planned for patch 4.14.1: repair legacy configuration startup, data and secret handling, Docker/frozen runtime paths, process/network/download reliability, locale compatibility, and binding release tests. These audit fixes remain open until implemented and verified; current product version is 4.14. See `docs/BUGFIX-PLAN.md`.

- Locally verified: legacy `params.json` migration no longer crashes on missing/invalid fields; Docker build context excludes local configuration and credential files. Release and Git persistence gates remain open.
- Locally verified: startup/completion cache cleanup rejects outside and symlinked paths; CLI now reserves distinct output and cache directories for every run, preserving prior exports and concurrent results.
- Locally verified: Docker WebUI listens on the host port and requires credentials; a fresh local image returned 401/200/401 for unauthenticated/valid/invalid access. Frozen desktop paths separate bundled resources from writable user data. A previous ZIP-extracted artifact passed read-only GUI and packaged media smoke.
- Locally verified: repaired the earlier missing `jaraco.text` package and bundled GUI modules loaded dynamically from menus. The rebuilt Python 3.12 candidate opens all 5 sidebar windows and all 72 dynamic menu windows; packaged provider/dialog, CLI, SRT and generated MP4 smoke pass. Clean Windows runner, full provider-backed media flow and release checks remain open.
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
