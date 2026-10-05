# Phase 4 ? Light workspace layout

## Planned extension — ENH-004

| Task | State | Gate |
| --- | --- | --- |
| 4.13 Subtitle correction operability and contrast | PASS | 9 focused, 20 related UI and 585 full Python 3.12 tests pass; implementation and handoff persisted to `dhsys/main` |
| 4.14 Explicit subtitle output | planned | Hard/soft/no-subtitle output is clear; hard pixels and soft stream are separately verified |
| 4.15 Basic navigation and provider profiles | planned | Basic tasks are compact; legacy actions/configuration remain compatible |
| 4.16 VieNeu pilot and En–Vi pronunciation control | planned | Local opt-in pilot and benchmark pass without modifying displayed SRT |
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

Phase state: in_progress. Tasks 4.1–4.12 and ENH-003 are verified locally; Git upstream persistence and the separate Phase 3 clean-runner/release gates remain open.

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
