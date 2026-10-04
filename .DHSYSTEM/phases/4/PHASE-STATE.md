# Phase 4 ? Light workspace layout

| Task | State | Gate |
| --- | --- | --- |
| 4.1 Existing workflow section cards | verified locally; persistence pending | 5 section cards preserve original widgets; source and packaged UI probes pass |
| 4.2 Workflow view state bridge | verified locally; persistence pending | Presentation-only mapping from action/`SignMsg` events to card state; source and frozen UI/resource probes pass |
| 4.3 Workflow hierarchy and action areas | verified locally; persistence pending | Numbered steps, presentation-only action/activity/subtitle areas, wrapping workflow rows, narrow navigation menu; 559 tests and deployed frozen smoke pass |
| 4.4 Light application shell and theme | verified locally; persistence pending | Existing workspace is reparented into shell; shared light QSS and 1280?720/1920?1080 smoke pass |
| 4.5 Navigation parity and workspace hierarchy | verified locally; persistence pending | Sidebar shortcuts and tool catalog reuse original QAction instances; focused Qt tests pass |
| 4.6 Regression evidence and handoff | verified locally; persistence pending | 10 focused UI tests and 549 full Python 3.12 tests pass; offscreen screenshots saved |
| 4.7 Rebuild and smoke-test light Windows candidate | verified locally; persistence pending | Python 3.12 candidate has light QSS; frozen/UI/sidebar/menu smoke pass |

Phase state: in_progress. Task 4.3 is active. Tasks 4.1–4.2 and the approved light-layout slice are verified locally. Phase 3 remains in progress, and its clean-runner, provider-media and upstream-persistence gates remain open.

## Evidence ? 2026-10-04

- `python -m pytest -q tests/test_light_workspace.py tests/test_vietnamese_home.py tests/test_ui_en_split.py --basetemp=.pytest-ui-tmp -p no:cacheprovider` ? 10 passed.
- `python -m pytest -q --basetemp=.pytest-full-ui-tmp -p no:cacheprovider` with `pytransvideo-runtime312` ? 549 passed; one upstream `pydub` Python 3.13 deprecation warning.
- Offscreen Qt smoke instantiated the generated workspace inside `WorkspaceShell` and saved `.DHSYSTEM/ui-direction/2026-10-04-light-workspace/workspace-1280x720.png` and `workspace-1920x1080.png`.

- Rebuilt `dist/sp/sp.exe` with Python 3.12.13 and staged the normal one-directory release layout. SHA-256: `8c3396a06c41fee7f59effb22a03a0175e1db38be3c4345d6cd3f3a8236a7e3d`. From `tmp/light-package-smoke-final`, frozen resource/provider/dialog/CLI/SRT/MP4 smoke passed; frozen UI smoke confirmed `WorkspaceShell` and `light.qss`; 5 sidebar and 71 dynamic-menu routes passed.

Local checkpoint `da883c6e` preserves this verified candidate evidence.
- Task 4.1: 11 focused UI tests and 550 full Python 3.12 tests passed. Offscreen 1280?720/1920?1080 smoke confirmed Start, subtitle and queue visibility. Rebuilt `dist/sp/sp.exe` SHA-256 `6b5d70b334489d976a5c96f54cf6d8a331cc523f9d80bd2a228d7a9faf1c816e`; frozen resource smoke and packaged UI probe passed, reporting 5 workflow sections and bundled light style.

Local checkpoint `f29af7af` preserves the verified workflow-section implementation.

- Task 4.2: focused Python 3.12 UI/state suite: 11 passed; full Python 3.12 suite: 554 passed with 5 external `pydub` warnings. Rebuilt `dist/sp/sp.exe` SHA-256 `A37D876AA535802538EBA223714DD3E830B95C633248B91EECEFF3A05829ED02`. Frozen resource/media and generated UI probes pass from isolated working storage; UI reports five sections and running workflow state.
