# Changelog

## Unreleased

Planned ENH-005 for the 4.15.0 line: add a GitHub-independent local distribution path with portable ZIP and per-user Setup.exe, plus a Vietnamese/English “Kiểm tra máy” surface that reports workload-specific CPU/RAM/disk/GPU/runtime readiness. Any remediation is explicit, allowlisted and re-verified; Python/Qt/FFmpeg stay bundled, while drivers/CUDA/large models remain guided or opt-in.

- ENH-005 Task 5.1 now provides a sanitized, workload-aware readiness service for Windows hardware/runtime checks. Basic CPU-only use remains supported, bundled FFmpeg/resources and writable app-data remain required, and Windows frozen first-run seeding now tolerates the `PermissionError` form of lock contention.

- ENH-005 Task 5.2 adds a read-only Vietnamese/English **Kiểm tra máy** desktop surface with workload-specific readiness cards, Refresh, sanitized Copy/Export support reports and frozen-route coverage. It does not install drivers, CUDA, models or other prerequisites; remediation remains a separate explicit-consent Task 5.3 flow.

- ENH-005 Task 5.3 adds consent-based remediation from an immutable allowlist: exact WinGet IDs only, explicit confirmation and cancellation, readable UAC/network/reboot/installer recovery, post-condition verification, redacted logs and credential-free HTTPS-only official fallback links. GPU drivers/CUDA and large models are never silently installed.

- ENH-005 Task 5.4 adds a GitHub-independent local shipping pipeline that produces a portable ZIP, per-user Setup.exe, manifest and SHA-256 sidecars from the verified frozen candidate, rejects credentials/user runtime data/build-machine path leakage, inventories bundled licenses, and automatically verifies the portable build from a fresh extracted path without Python on `PATH`. Recipient-machine install/upgrade/uninstall lifecycle testing remains Task 5.5.

Planned for 4.15.0 (ENH-003, after the pending 4.14.1 repair release): offer Vietnamese and English as the only application UI/message locales while retaining Chinese speech recognition, translation, subtitle and voice support. Tasks 4.9–4.12 are verified locally; the current manifest remains 4.14.

- Subtitle correction dialogs now allow normal mouse and keyboard editing, use a readable light-table palette, show unsaved changes, and wait for an explicit save, discard or cancel action instead of auto-closing on a countdown.

- Fresh desktop video-translation tasks now default to subtitles that are always visible on the video while preserving every legacy `subtitle_type` value. Soft/no-subtitle choices are explicit, no-subtitle export warns before starting, and successful jobs show a receipt with subtitle mode, video/SRT paths, bilingual order and the soft-track player instruction.

- Basic desktop navigation now exposes task-first media actions plus reversible Local/Gemini/Advanced provider profiles without deleting providers, renumbering persisted IDs or erasing saved credentials. Local-only status requires a loopback endpoint; remote profiles retain privacy, quota/rate-limit and fallback guidance.

- Vietnamese TTS pronunciation control now uses transient `tts_text` plus an optional per-project glossary, leaving displayed/persisted SRT unchanged. VieNeu remains an opt-in local OpenAI-compatible pilot; discovered voices stay selectable for content-specific and multi-speaker dubbing, with Hải Đăng recorded as the preferred pilot voice rather than a forced default.

- ENH-004 end-to-end acceptance now covers the current Windows candidate as well as source tests: 72 focused, 349 related and 658 full Python 3.12.14 tests pass; frozen core/UI/sidebar/menu smoke passes; hard subtitles are visible in decoded frames and soft subtitles contain one Vietnamese `mov_text` track. Independent Phase 3 release gates remain open.

- Desktop UI now loads and packages only Vietnamese and English locales; saved Chinese UI settings migrate to English, while Chinese media languages and voices remain available.

- Application-authored desktop status, errors, settings and provider dialogs now use Vietnamese or English. CLI output exposes only Vietnamese and English, and WebUI follows the shared locale allowlist without removing Chinese media language codes or voices.

- Windows packaging now includes the faster-whisper Silero VAD model, the `zhconv` dictionary, and the Microsoft translation fallback used when Google is unavailable. An isolated candidate passed Vietnamese, English and legacy-Chinese locale probes plus a packaged Mandarin-to-Vietnamese recognition, translation, Edge TTS and MP4 output flow.

- The home page and four primary quick tools now fit narrow desktop windows; Multiple speakers follows the light table style, and compact Vietnamese navigation reads “Danh mục”. Existing routes and processing behavior remain unchanged.

- The workspace now has one visible Home route: the sidebar on wide desktops and its compact Menu equivalent on narrow desktops.

- The desktop workflow now wraps configuration controls, scrolls vertically when needed, and replaces the full sidebar with a compact menu on narrow desktops. Existing controls and actions are unchanged.

- Frozen Windows startup now seeds bundled assets only when absent and serializes first-run copying, preventing `WinError 32` when a shared AppData asset is already in use.

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
