# Phase 4 ? Light workspace layout

| Task | State | Gate |
| --- | --- | --- |
| 4.1 Existing workflow section cards | in_progress | Preserve all original widgets and handlers while grouping the five rows |
| 4.4 Light application shell and theme | verified locally; persistence pending | Existing workspace is reparented into shell; shared light QSS and 1280?720/1920?1080 smoke pass |
| 4.5 Navigation parity and workspace hierarchy | verified locally; persistence pending | Sidebar shortcuts and tool catalog reuse original QAction instances; focused Qt tests pass |
| 4.6 Regression evidence and handoff | verified locally; persistence pending | 10 focused UI tests and 549 full Python 3.12 tests pass; offscreen screenshots saved |
| 4.7 Rebuild and smoke-test light Windows candidate | verified locally; persistence pending | Python 3.12 candidate has light QSS; frozen/UI/sidebar/menu smoke pass |

Phase state: in_progress. The approved light-layout slice, including a rebuilt local Windows candidate, is verified locally. Task 4.1 is in progress; the remaining wider Phase 4 workflow redesign remains planned. Phase 3 remains in progress, and its clean-runner, provider-media and upstream-persistence gates remain open.

## Evidence ? 2026-10-04

- `python -m pytest -q tests/test_light_workspace.py tests/test_vietnamese_home.py tests/test_ui_en_split.py --basetemp=.pytest-ui-tmp -p no:cacheprovider` ? 10 passed.
- `python -m pytest -q --basetemp=.pytest-full-ui-tmp -p no:cacheprovider` with `pytransvideo-runtime312` ? 549 passed; one upstream `pydub` Python 3.13 deprecation warning.
- Offscreen Qt smoke instantiated the generated workspace inside `WorkspaceShell` and saved `.DHSYSTEM/ui-direction/2026-10-04-light-workspace/workspace-1280x720.png` and `workspace-1920x1080.png`.

- Rebuilt `dist/sp/sp.exe` with Python 3.12.13 and staged the normal one-directory release layout. SHA-256: `8c3396a06c41fee7f59effb22a03a0175e1db38be3c4345d6cd3f3a8236a7e3d`. From `tmp/light-package-smoke-final`, frozen resource/provider/dialog/CLI/SRT/MP4 smoke passed; frozen UI smoke confirmed `WorkspaceShell` and `light.qss`; 5 sidebar and 71 dynamic-menu routes passed.

Local checkpoint `da883c6e` preserves this verified candidate evidence.
