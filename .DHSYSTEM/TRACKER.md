# Tracker

- Complete and persisted: ENH-004 task 4.17 — compatibility-first provider/data-plane policy is implemented. No provider is deleted, renumbered or hidden; Advanced/Custom and exact saved IDs are preserved. Local-only status requires a loopback Local LLM endpoint; invalid/non-loopback Local activation is rejected without changing prior provider indexes. Gemini/OpenRouter are disclosed as remote/off-device with quota/rate-limit and non-destructive fallback guidance. Chinese media-language support remains unchanged. Evidence: 17 focused, 151 related and 658 full Python 3.12 tests pass; implementation checkpoint `26a24591`, closeout `ada51c14` persisted to `origin/main`.

- Complete and persisted: ENH-004 task 4.16 — non-destructive Vietnamese–English pronunciation control is implemented; local VieNeu voice discovery fills the existing selector without changing the OpenAI TTS provider ID or saved role mapping, and Multiple speakers can assign distinct voices per line/speaker. The 25/25 audition is complete, `Hải Đăng` is the preferred pilot voice, and its 12/12 benchmark has 12/12 hashes rechecked, mean duration ratio `0.502` and `1/12` within ±20%. On 2026-10-06 the user accepted pronunciation accuracy, naturalness and voice continuity for that pilot fixture set. Closeout revalidation passed 44 core focused, 94 related TTS/config/UI and 642 full Python 3.12 tests (one external `pydub` warning). Closeout commit `0b4f270b` is persisted to `origin/main`; VieNeu remains opt-in and OmniVoice absence remains a supported-hardware skip.

- Complete: ENH-004 task 4.15 — the basic workspace has five media jobs plus advanced tools; provider settings are separate from “All tools”; reversible local/Gemini/custom profiles keep legacy provider IDs and credentials intact and restore prior custom selections. Tests: 11 focused, 35 related UI/config and 621 full Python 3.12 with one external warning. Completion commit `a9aee380` and both 4.15 tags are persisted to GitHub.

- Complete: ENH-004 task 4.14 — fresh translated-video tasks default to always-visible hard subtitles without changing legacy enum values; no-subtitle output is explicit, completion receipts report paths/mode, and hard/soft media contracts are verified. Tests: 38 focused, 104 related UI, 2 real pipeline media and 613 full Python 3.12 with one external warning. Commit `93497188` and both 4.14 tags are persisted to GitHub; Task 4.15 is next.

- Complete: ENH-004 task 4.13 — both subtitle correction dialogs are focusable, selectable and editable; countdown auto-close is removed; light contrast and explicit unsaved state are applied. Tests: 9 focused, 20 related UI, 585 full Python 3.12 with one external warning. Commits are persisted to `dhsys/main`.

- Active: [ENH-004](requests/ENH-004.md) — Vietnamese-first video workflow (Phase 4 tasks 4.13–4.18). Tasks 4.13–4.17 are PASS and persisted; 4.18 end-to-end source/frozen Windows/media handoff is in progress. This work does not supersede the active Phase 3 release gate.

- Active: [ENH-003](requests/ENH-003.md) — UI Việt/Anh, giữ xử lý nội dung tiếng Trung (P1; tasks 4.9–4.12 verified locally; persistence pending).

- Current phase: 3 — supported runtime and Windows packaging
- Current task: 3.3 — clean-runner release gate and documentation
- Parallel UI task: 4.12 packaged locale and Chinese-media regression verified locally (576 Python 3.12 tests); tasks 4.1–4.12 verified locally; persistence pending
- State: 3.1–3.2 and 3.4–3.9 verified locally; 3.3 in_progress with the frozen startup contention repair verified locally; phases 1–2 verified locally; local Git checkpoint exists but upstream persistence is pending
- Local branch/checkpoint: `codex/phase3-release-gate`; `fbcd924f` preserves the prior Phase 1–3 changes, later commits contain the release gate; no upstream is configured for this branch
- Planned patch version: 4.14.1 (not yet applied to product manifest)
- Planned Phase 4 localization target: 4.15.0 after the 4.14.1 repair release; current manifest remains 4.14 until implementation and release gates pass.
- Starting commit: `8cf344fe`
- Input artifacts: `docs/PLAN.md`, `docs/SPEC.md`, `docs/BUGFIX-PLAN.md`, `.DHSYSTEM/audit-report.md`, `.DHSYSTEM/requests/`, `docs/brainstorm/session-2026-10-03.md`

## Evidence

- ENH-003 completion evidence 2026-10-05: 576 Python 3.12.13 tests pass with one external warning. Candidate `tmp/enh003-localized-dist/sp/sp.exe` SHA-256 `9EFE5C00A69E182D896F0B91A5F8B28FF0A7F2EE49B284DAC6962939821ECB6` passes frozen VAD/`zhconv`/provider/resource smoke and vi/en/legacy-zh UI probes. A 7.296-second Mandarin clip completed packaged faster-whisper `tiny` recognition, Microsoft translation fallback after Google 429, Vietnamese Edge TTS 2/2, and H.264/AAC/subtitle MP4 output; forbidden Chinese application labels were absent. Branch upstream persistence and Phase 3 release gates remain open.

- Packaged faster-whisper VAD repair 2026-10-05: the shipped `dist/sp` lacked `_internal/faster_whisper/assets/silero_vad_v6.onnx` although the Python environment had it. The new frozen smoke reproduced the failure before the repair, then loaded the ONNX model after a local asset copy. `sp.spec` now collects that exact package asset and the candidate workflow checks its presence. A fresh isolated PyInstaller build at `tmp/vad-fixed-dist/sp` passed frozen smoke. A 12-second excerpt of the reported FreeRTOS video passed packaged CPU `tiny` transcription with `vad_filter=True` and produced 3 segments in both the fresh build and the patched `dist/sp`. Python 3.12 source suite: 563 passed, 1 external deprecation warning. Full translation/TTS/media output, clean runner and upstream release gates remain open.

- Task 4.8 responsive completion 2026-10-04: home cards reflow to one column below 760 px; four core quick tools fit 480 px; Multiple speakers follows the shared light table style; compact Vietnamese navigation reads “Danh mục”. Focused tests: 11 passed; full Python 3.12 suite: 563 passed with one external `pydub` warning. Candidate and deployed `dist/sp/sp.exe` SHA-256 `2C52AF073F2A148E60C82340DFAE5A198EAF6E01F5AEC7AE0303D7684061F094` passed frozen UI and resource/provider/dialog/CLI/SRT/MP4 smoke from fresh user data.

- Navigation de-duplication 2026-10-04: the legacy menu-bar and status-bar Home controls are hidden; sidebar Home remains the desktop route and its compact-menu equivalent remains at narrow width. Focused navigation: 27 passed; full Python 3.12: 560 passed with one existing external `pydub` warning. Candidate and deployed `dist/sp/sp.exe` SHA-256 `3F6C8B89DB50D1C91F0E8BC73E1E1E9CFE483BE820596B0A082656F87582CD12` passed frozen UI and resource/provider/dialog/CLI/SRT/MP4 smoke.


- Responsive workspace repair 2026-10-04: workflow rows wrap instead of compressing, the workflow pane scrolls vertically, the subtitle pane can shrink, and navigation collapses into a menu below 980 px while reusing existing QAction instances. Focused UI: 11 passed; full Python 3.12: 559 passed with one existing external `pydub` warning. Source screenshots at 1280?720, 1024?720 and 900?720 are stored in `.DHSYSTEM/ui-direction/2026-10-04-light-workspace/`. Candidate `tmp/responsive-dist/sp/sp.exe` SHA-256 `B4CF72937F57790380018A4571731FA16C18340BE51D10099C06504AE59FF827` passed frozen resource/provider/dialog/CLI/SRT/MP4 and responsive UI smoke; concurrent startup smoke passed. The candidate was synchronized to `dist/sp`; the deployed resource and responsive UI smoke checks passed.

- Frozen startup contention repair 2026-10-04: the path initializer no longer overwrites the shared icon on every launch. Missing bundled assets are seeded through an exclusive lock and atomic destination replacement. `tests/test_frozen_paths.py` plus `tests/test_config_split.py`: 39 passed; full Python 3.12 suite: 557 passed with one existing external `pydub` warning. Candidate SHA-256 `05AB4C46E56A3042A5876119A4710A1C6C068F33376A24D98A69170994CC3EE3` started twice concurrently with one isolated `LOCALAPPDATA`; both returned 0 and passed resource, provider/dialog, CLI, SRT and generated MP4 smoke checks. The verified package was synchronized to `dist/sp` and the same two-process smoke passed again there. Clean runner, full provider media and upstream persistence remain open.

- Task 4.2 workflow view state 2026-10-04: a pure presentation mapper receives existing action status and `SignMsg.type`, without changing queue, media, settings, output, dialog or CLI behavior. Focused Python 3.12 UI/state tests: 11 passed; full suite: 554 passed. Rebuilt candidate `dist/sp/sp.exe` SHA-256 `A37D876AA535802538EBA223714DD3E830B95C633248B91EECEFF3A05829ED02` passed frozen resource/media and UI probes; the UI probe reported five sections and `workflow_state: running`.

- Task 4.1 workflow cards 2026-10-04: existing preparation, transcription, translation, voice/subtitles and timing/output controls are grouped without changing their object names or handlers. Focused UI: 11 passed; full Python 3.12: 550 passed. Rebuilt candidate `dist/sp/sp.exe` SHA-256 `6b5d70b334489d976a5c96f54cf6d8a331cc523f9d80bd2a228d7a9faf1c816e` passed frozen resource and UI probes with 5 sections.


- Phase 4 packaged light candidate 2026-10-04: Python 3.12.13 rebuild at `dist/sp/sp.exe` contains `light.qss`; SHA-256 `8c3396a06c41fee7f59effb22a03a0175e1db38be3c4345d6cd3f3a8236a7e3d`. Frozen resource/provider/dialog/CLI/SRT/MP4 smoke, frozen WorkspaceShell/UI smoke, 5 sidebar routes and 71 dynamic-menu routes pass from an isolated CWD. Clean runner, live provider-media and upstream persistence remain open.


- Phase 4 light-layout slice 2026-10-04: white/gray/`#14452F` stylesheet, light launch/home/about surfaces and `DHSYSTEM.SYS` identity applied without changing processing code. `WorkspaceShell` reparents the original generated workspace and its sidebar triggers the same QAction objects. Focused UI suite: 10 passed; full Python 3.12 suite: 549 passed. Offscreen 1280?720 and 1920?1080 workspace smoke screenshots saved. Local checkpoint `4e5d93fb` preserves this slice; the broader Phase 4 redesign and all Phase 3 release gates remain open.


- Sidebar audit 2026-10-04: BUG-016 reproduced on the older executable (5/5 sidebar failures, 65/72 dynamic menu imports missing). The new Python 3.12 candidate opens 5/5 sidebar and 72/72 dynamic menu windows; packaged provider/dialog, CLI, SRT, generated MP4 and 15-second GUI startup smoke pass from the copied delivery directory. Python 3.12 suite: 540 passed. The candidate workflow now checks those routes on the extracted package. Clean Windows runner, full provider-backed media workflow and upstream persistence remain open.

- Continuation on 2026-10-04: Python 3.12.13 final onedir rebuild passed executable provider/dialog, CLI `--version`, SRT parser and FFmpeg MP4 audio/video smoke. `Compress-Archive` failed with `OutOfMemoryException` on the 6.38 GB tree, so the workflow uses `tar.exe`; its 3.69 GB ZIP passed SHA-256 and `Expand-Archive`. The extracted app passed the same smoke with NTFS content writes denied and launched the GUI twice from another CWD, storing user data outside the install. Docker host-port/auth smoke also passed locally. Clean runner, full provider-backed media and upstream persistence remain release gates.

- Continuation on 2026-10-04: Python 3.12.13 full suite 540 passed; Docker image rebuilt from the current workspace and host-port/auth probe returned 401 without login, 200 with valid login, 401 with wrong credentials. Network bind without credentials exits with an error. Packaged script probe on the older Python 3.12 artifact exposed missing `jaraco.text` in `pkg_resources` before app startup; task 3.2 remains in progress while `sp.spec` is corrected and rebuilt.

- Task 3.3 on 2026-10-04: runtime documentation and state records reconciled. The Python 3.12 artifact starts twice headlessly with temporary user data and staged FFmpeg. Focused release-path suite: 97 passed; lock/YAML/diff checks pass. Docker daemon is unavailable, and clean-runner, packaged provider/media, checksum and Git persistence gates remain open.

- Task 3.2 on 2026-10-04: Python 3.12 PyInstaller creates the onedir artifact and it starts headlessly; resources and staged FFmpeg layout verified. Python 3.10 crashes in the torchaudio hook, so the candidate workflow now uses tested 3.12. Clean runner, packaged dynamic provider, and media smoke remain open.

- Task 3.1 on 2026-10-04: locked Python 3.10.19, 3.11.15, 3.12.13 environments with `wetext` each pass 540 tests; CLI and offscreen GUI import pass. FFmpeg pinned archive SHA-256 matches and short MP4 has audio/video. Chatterbox/Perth are pinned to commits; `uv lock --check --offline` passes (424 packages). Audit/debug repaired invalid escape warnings and isolated a test harness pipe exit. Clean Windows artifact and Git persistence gates remain open.

- Task 3.9 on 2026-10-04: saved language codes resolve to valid WebUI dropdown choices and voice roles; desktop short locale flags are parsed before config import. Qt/CLI tests now invoke product behavior. Focused 102/full Python 3.10 540 tests pass. Audit/debug removed a trailing blank line; Git persistence and packaged media smoke remain open.

- Task 3.8 on 2026-10-04: global Hugging Face monkeypatch removed; model cache/downloads validate size/hash and reject one-byte model files. Local HTTP artifact/reuse and concurrent callback probes pass. Focused 7/full Python 3.10 546 tests pass. Audit/debug closed a one-byte matching-Length gap. Git persistence remains open.

- Task 3.7 on 2026-10-04: valid CA preserved, invalid CA rejected with named setting; only app-descendant FFmpeg terminated. Live probe left unrelated PID 17904 running while owned process stopped, then cleaned up probe. Focused 7/full 539 Python 3.10 tests pass. Audit found no new task-scope failure; Git persistence and packaged GUI smoke remain open.

- Task 3.6 on 2026-10-04: 534 Python 3.10 tests pass, frozen import from another CWD leaves install tree untouched, Docker entry/auth contract is covered. Audit/debug repaired missing user-data directory and filename-loaded FunASR helper path. Docker image build restarted with webui-only extra; real container and extracted Windows artifact smoke are pending, so task stays in_progress.

- Task 3.5 on 2026-10-04: shared guarded cache cleanup, unique CLI run directories and per-run cache; 88 focused/528 full Python 3.10 tests passed. Audit found no new task-scope failure, so no debug repair was needed. Git persistence remains open.

- Task 3.4 on 2026-10-04: legacy config regression tests 5 passed, full Python 3.10 suite 523 passed, scratch Docker context image excluded dummy environment secret and local params/cfg files. Audit found no remaining task 3.4 product failure; debug fixed a test-only missing dependency. Git persistence remains open, so no PASS/release claim.

- Audit repair planning 2026-10-04: 15 BUG and 1 ENH request mapped to Phase 3 tasks 3.4–3.9, 3.1–3.3. No audit finding is marked fixed by this planning update. The queue and G3a–G3c release criteria are in `docs/BUGFIX-PLAN.md`.

- Initial audit host had Python 3.14.0 and 3.12.13 while the original manifest pinned 3.10; later local manifest now allows 3.10–3.12, with optional `wetext` still constrained to cp310 on Windows.
- Prior host run: 4 test collection errors; a focused subset had 39 passing and 3 failing tests on Python 3.14.
- Python 3.10.19 environment installed; `uv lock --check` passed and 394 packages installed.
- Full collection: 3 stale imports. Excluding those files: 416 tests passed, 60 failed, 0 setup errors with a workspace basetemp.
- Task 1.1 is locally verified; git persistence is pending, so it is not marked PASS.
- All 488 collected tests now pass on Python 3.10.19; the only warning is FFmpeg absent from the current PATH. CLI `--version` reports 4.14 and install docs match the `webui` extra.
- Existing provider index numbers changed before this work while the UI persists `translate_type` as a number. This needs a migration decision before public upgrade; current numbers are frozen by tests.
- VibeVoice parser no longer evaluates response text. Eleven focused parser tests and the full 499-test suite pass.
- Removed hardcoded TLS bypasses from 16 modules. A static certificate-verification policy test and an HTTPS adapter test pass.
- WebUI now defaults to loopback, requires authentication for network/share mode, and excludes logs/config/old files from downloads. Full suite: 512 passed.
- Cache cleanup now rejects paths outside the managed temp root, WebUI preserves prior runs, and `only_out_mp4` keeps prior exports on collision. Full suite: 517 passed.
- Review on 2026-10-04: Nemotron's runtime manifest supports 3.10–3.12; isolated Python 3.12 core install and 518 tests passed. Python 3.10 also passes 518 tests. `wetext` fails on Python 3.12 because its Windows Pynini wheel is cp310. The initial packaging workflow referenced ignored `sp.spec`, expected an onedir path from a onefile spec, and attempted automatic release; those static defects are corrected locally. A real CLI `--help` crash and lost Chinese CLI messages were corrected with a regression test. Candidate runner build and packaged smoke are still required. The incoming WebUI English translation needs product review. Fresh offline lock verification is blocked by the existing mutable Chatterbox source URL.
