# Phase 4 ? Light workspace layout

## Planned extension — ENH-004

| Task | State | Gate |
| --- | --- | --- |
| 4.13 Subtitle correction operability and contrast | PASS | 9 focused, 20 related UI and 585 full Python 3.12 tests pass; implementation and handoff persisted to `dhsys/main` |
| 4.14 Explicit subtitle output | PASS | 38 focused, 104 related UI, 2 real pipeline media and 613 full Python 3.12 tests pass |
| 4.15 Basic navigation and provider profiles | PASS | 11 focused, 35 related UI/config and 621 full Python 3.12 tests pass; reversible legacy-ID profiles verified |
| 4.16 VieNeu pilot and En–Vi pronunciation control | in_progress | Non-destructive pronunciation layer, local voice discovery, 25-voice audition set and Edge/VieNeu 12-fixture live benchmarks verified; human listening gate remains open |
| 4.17 Controlled provider reduction | planned | Migration, privacy and local-only behavior are proven before any removal |
| 4.18 End-to-end handoff | planned | Source/frozen Windows evidence and documentation cover 4.13–4.17 |

| Task | State | Gate |
| --- | --- | --- |
| 4.1 Existing workflow section cards | verified locally; persistence pending | 5 section cards preserve original widgets; source and packaged UI probes pass |
| 4.2 Workflow view state bridge | verified locally; persistence pending | Presentation-only mapping from action/`SignMsg` events to card state; source and frozen UI/resource probes pass |
| 4.3 Workflow hierarchy and action areas | verified locally; persistence pending | Responsive rows/menu, one visible Home route; 560 tests and deployed frozen smoke pass |
| 4.4 Light application shell and theme | verified locally; persistence pending | Existing workspace is reparented into shell; shared light QSS and 1280?720/1920?1080 smoke pass |
| 4.5 Navigation parity and workspace hierarchy | verified locally; persistence pending | Sidebar shortcuts and tool catalog reuse original QAction instances; focused Qt tests pass |
| 4.6 Regression evidence and handoff | verified locally; persistence pending | 10 focused UI tests and 549 full Python 3.12 tests pass; offscreen screenshots saved |
| 4.7 Rebuild and smoke-test light Windows candidate | verified locally; persistence pending | Python 3.12 candidate has light QSS; frozen/UI/sidebar/menu smoke pass |
| 4.8 Responsive home and core utility surfaces | verified locally; persistence pending | Home cards, core quick tools, light-table parity and compact Vietnamese navigation at 480/720/900/1280 px |
| 4.9 Two UI locales and legacy migration | verified locally; persistence pending | `vi_VN`/`en_US` allowlist; old Chinese UI settings migrate; Chinese media codes preserved; 567 source tests pass |
| 4.10 Application-authored runtime messages | verified locally; persistence pending | Task summary, progress, errors, settings and provider dialogs use Vietnamese/English; Chinese media text untouched |
| 4.11 CLI/WebUI locale parity | verified locally; persistence pending | CLI exposes only Vietnamese/English; WebUI uses the shared locale allowlist; Chinese remains source/target content language |
| 4.12 Packaged and Chinese-media regression | verified locally; persistence pending | 576 tests; frozen vi/en/legacy migration; VAD/zhconv; packaged Mandarin → Vietnamese STT/translation/TTS/MP4 flow pass |

Phase state: in_progress. Tasks 4.1–4.15 and ENH-003 are verified; Task 4.15 is persisted to `origin/main` at `a9aee380`, and Task 4.16 is now in progress. The separate Phase 3 clean-runner/release gates remain open.

## Task 4.16 evidence — 2026-10-05

- Vietnamese-only transient `tts_text` keeps displayed/persisted SRT unchanged while provider-facing text and TTS cache keys use the prepared pronunciation form. Project glossary precedence is deterministic and legacy provider/model IDs are untouched.
- Local VieNeu voice discovery is restricted to loopback plus a VieNeu model name, keeps any saved roles first, falls back safely when discovery fails, and does not change the persisted OpenAI TTS provider ID/index. The main voice selector preserves a selected discovered voice across refreshes.
- The existing Multiple speakers dialog can assign different VieNeu voices to different speakers/lines; dubbing consumes those per-line roles without changing subtitle text. This provides the male/female dubbing foundation without adding a new provider ID.
- A 25/25 audition set was generated from the same 10-word sentence, `Xin chào, đây là giọng thử cho nội dung dịch.` Compact non-sensitive metadata is stored in `.DHSYSTEM/phases/4/evidence/4.16-vieneu-voice-audition.json`; local WAVs remain ignored under `tmp/` and are not committed.
- Focused pronunciation/BaseTTS/benchmark/voice-selection tests: 53 passed. Related TTS/config/UI tests: 185 passed. Full Python 3.12 suite: 642 passed; the full run has one external `pydub` deprecation warning.
- Edge live benchmark generated all 12 required fixtures. Compact hashes/metrics are stored in `.DHSYSTEM/phases/4/evidence/4.16-edge-benchmark.json`; listening metrics remain pending human review.
- VieNeu v3 Turbo ONNX/CPU ran successfully on loopback through the existing OpenAI-compatible adapter and generated all 12 required fixtures. Compact hashes/metrics are stored in `.DHSYSTEM/phases/4/evidence/4.16-vieneu-benchmark.json`; the 12 WAV hashes were rechecked with zero mismatches.
- The benchmark script now runs directly from the repository root without a manual `PYTHONPATH`, matching the documented command. OmniVoice's local model remains absent and is a supported-hardware skip.
- Pronunciation accuracy, naturalness, voice continuity and the user's preferred main VieNeu voice are still pending human listening review for the live outputs, so Task 4.16 is not PASS and Task 4.17 must not start.

## Task 4.15 evidence — 2026-10-05

- The basic workspace exposes five media jobs plus the advanced entry; every pre-existing QAction remains reachable through the advanced catalog or provider settings.
- Provider profiles use existing numeric IDs only, preserve stored credentials, snapshot/restore the prior custom selection, and keep provider configuration outside “All tools”.
- The remote Gemini profile confirms data-policy/privacy, quota and fallback information before apply. The local/basic path does not require cloud credentials.
- Python 3.12.14: 11 focused tests, 35 related UI/config tests and 621 full tests pass; the only full-suite warning is external `pydub` use of deprecated `audioop`.
- Completion checkpoint `a9aee380` plus tags `pyVideoTrans-DH-p4-t4.15` and `pyVideoTrans-DH-p4-t4.15-done` are present on the GitHub remote.
- Phase 3 clean-runner, provider-backed media and release gates remain independent and open.

## Task 4.14 evidence — 2026-10-05

- Fresh desktop settings use persisted value `1` (always-visible hard subtitles); valid legacy values `0..4` round-trip unchanged. The standard video mode no longer switches silently to extraction/no-subtitle mode, and explicit no-subtitle output requires confirmation.
- Completion receipts show mode, video/SRT paths, bilingual order and the instruction to enable the subtitle track for soft-subtitle video.
- Product-pipeline FFmpeg fixtures pass: hard subtitles change decoded frame pixels; soft subtitles contain exactly one `mov_text` stream tagged `vie` by `ffprobe`. Bilingual hard/soft fixtures retain both source/target orders.
- Python 3.12.14: 38 focused state/UI tests, 104 related UI/config/task tests, 2 media tests and 613 full tests pass; the only full-suite warning is external `pydub` use of deprecated `audioop`.
- Commit `93497188` plus tags `pyVideoTrans-DH-p4-t4.14` and `pyVideoTrans-DH-p4-t4.14-done` are present on the GitHub remote.
- Phase 3 clean-runner, provider-backed media and release gates remain independent and open.

## Task 4.12 evidence — 2026-10-05

- Full Python 3.12.13 source suite: 576 passed with one external `pydub` warning. `git diff --check` and the application-authored runtime Han scan passed.
- Isolated Windows candidate SHA-256 `9EFE5C00A69E182D896F0B91A5F8B28FF0A7F2EE49B284DAC6962939821ECB6` passed frozen resource smoke, including Silero VAD, `zhconv`, Google/Microsoft dynamic providers, only `vi_VN`/`en_US` catalogs, and retained `zh-cn`/`zh-tw`/`yue` media codes.
- Frozen UI passed in Vietnamese and English. A legacy `zh_CN` setting plus user catalog migrated to `en_US`, preserved the two-choice allowlist, and ignored the old catalog.
- Packaged 7.296-second Mandarin `zh-cn` → Vietnamese flow passed with faster-whisper `tiny`, Microsoft translation fallback after Google returned 429, Edge TTS 2/2, source/target SRT, and an H.264/AAC/`mov_text` MP4. No forbidden Chinese application labels appeared in the logs.

## Task 4.11 evidence — 2026-10-05

- The CLI runtime catalog contains only Vietnamese and English, maps legacy Chinese UI locale aliases to English, and preserves Chinese media codes and voice identifiers in examples and task parameters.
- WebUI no longer overrides the shared configured locale with English. The shared locale resolver restricts it to `vi_VN`/`en_US`; its interface source has no Han-character text.
- Focused CLI/WebUI/language suite: 109 passed. Full Python 3.12 source suite: 575 passed with one external `pydub` deprecation warning. Frozen verification remains task 4.12.

## Task 4.10 evidence — 2026-10-05

- Task summaries, runtime progress/errors, settings, provider dialogs, and the legal notice are Vietnamese or English. Locale-bound task configuration keeps Chinese media language codes and voice identifiers unchanged.
- A source scan retained only Chinese comments, match tokens for external operating-system errors, punctuation/normalization data, and model/provider media content.
- Focused locale/task/error suite: 72 passed. Full Python 3.12 source suite: 572 passed, with one external `pydub` deprecation warning. `git diff --check` passed. Frozen-package, CLI/WebUI, legacy-migration and Chinese-media regression remain open under 4.11–4.12.

## Task 4.9 evidence — 2026-10-05

- Only `vi_VN` and `en_US` UI catalogs are loaded or bundled; saved `zh_CN`/`zh` aliases migrate to English without changing other settings. The new install default is Vietnamese.
- Home exposes two UI locales; legacy Chinese launch flags select English, and proxy controls remain available in both supported locales. Chinese source/target and Edge voice codes remain present.
- Focused locale/config/home suite: 45 passed. Full Python 3.12 source suite: 567 passed, one external `pydub` warning. `git diff --check` passed. Frozen package verification belongs to task 4.12.

## Task 4.8 evidence — 2026-10-04

- Focused responsive Qt tests: 11 passed. Full Python 3.12 suite: 563 passed with one external `pydub` warning.
- Candidate and deployed `dist/sp/sp.exe` SHA-256 `2C52AF073F2A148E60C82340DFAE5A198EAF6E01F5AEC7AE0303D7684061F094` passed frozen UI smoke with the four core routes and 480/720/900/1280 px probes. Candidate frozen resource/provider/dialog/CLI/SRT/MP4 smoke also passed from fresh user data.

## Evidence ? 2026-10-04

- `python -m pytest -q tests/test_light_workspace.py tests/test_vietnamese_home.py tests/test_ui_en_split.py --basetemp=.pytest-ui-tmp -p no:cacheprovider` ? 10 passed.
- `python -m pytest -q --basetemp=.pytest-full-ui-tmp -p no:cacheprovider` with `pytransvideo-runtime312` ? 549 passed; one upstream `pydub` Python 3.13 deprecation warning.
- Offscreen Qt smoke instantiated the generated workspace inside `WorkspaceShell` and saved `.DHSYSTEM/ui-direction/2026-10-04-light-workspace/workspace-1280x720.png` and `workspace-1920x1080.png`.

- Rebuilt `dist/sp/sp.exe` with Python 3.12.13 and staged the normal one-directory release layout. SHA-256: `8c3396a06c41fee7f59effb22a03a0175e1db38be3c4345d6cd3f3a8236a7e3d`. From `tmp/light-package-smoke-final`, frozen resource/provider/dialog/CLI/SRT/MP4 smoke passed; frozen UI smoke confirmed `WorkspaceShell` and `light.qss`; 5 sidebar and 71 dynamic-menu routes passed.

Local checkpoint `da883c6e` preserves this verified candidate evidence.
- Task 4.1: 11 focused UI tests and 550 full Python 3.12 tests passed. Offscreen 1280?720/1920?1080 smoke confirmed Start, subtitle and queue visibility. Rebuilt `dist/sp/sp.exe` SHA-256 `6b5d70b334489d976a5c96f54cf6d8a331cc523f9d80bd2a228d7a9faf1c816e`; frozen resource smoke and packaged UI probe passed, reporting 5 workflow sections and bundled light style.

Local checkpoint `f29af7af` preserves the verified workflow-section implementation.

- Task 4.2: focused Python 3.12 UI/state suite: 11 passed; full Python 3.12 suite: 554 passed with 5 external `pydub` warnings. Rebuilt `dist/sp/sp.exe` SHA-256 `A37D876AA535802538EBA223714DD3E830B95C633248B91EECEFF3A05829ED02`. Frozen resource/media and generated UI probes pass from isolated working storage; UI reports five sections and running workflow state.
