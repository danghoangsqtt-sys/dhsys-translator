# Phase 3 — Runtime and Windows package

| Task | State | Gate |
| --- | --- | --- |
| 3.4 Legacy config and Docker secrets | verified locally; persistence pending | 5 focused and 523 full tests pass; scratch image excludes dummy secret/config |
| 3.5 Cache and CLI output preservation | verified locally; persistence pending | 88 focused and 528 full tests pass; outside files and reruns preserved |
| 3.6 Docker access and frozen paths | in_progress; artifact gates open | 534 tests and frozen import simulation pass; container/artifact smoke pending |
| 3.7 CA bundle and FFmpeg ownership | verified locally; persistence pending | 7 focused/539 full tests pass; live owned/unrelated FFmpeg smoke passes |
| 3.8 Model download integrity and concurrency | verified locally; persistence pending | 7 focused/546 full tests pass; real local HTTP and concurrent callback smoke pass |
| 3.9 Language and binding tests | verified locally; persistence and artifact smoke pending | 102 focused and 540 full tests pass; saved locale and real Qt/CLI bindings verified |
| 3.1 Python compatibility matrix | verified locally; artifact and persistence gates pending | 3.10/3.11/3.12 locked installs with wetext, 540 tests each; FFmpeg hash/media smoke |
| 3.2 Windows packaging pipeline | in_progress (review correction) | Clean runner builds and bundles required resources |
| 3.3 Release gate and documentation | in_progress | Local artifact starts; runner, Docker, media and persistence gates remain open |

Execution order: **3.4 → 3.5 → 3.6 → 3.7 → 3.8 → 3.9 → 3.1 → 3.2 → 3.3**. Existing 3.1/3.2 edits remain in progress, but their completion is gated by audit remediation and artifact checks. See `docs/BUGFIX-PLAN.md` and `.DHSYSTEM/requests/` for acceptance per finding. Planned patch version: 4.14.1; current product version remains 4.14.

Phase state: in_progress. Phases 1–2 are locally verified but the `dh-auto` git persistence gate remains unresolved because `origin` is the upstream `jianchang512/pyvideotrans` repository.

Review 2026-10-04: Python 3.10, 3.11 and 3.12 each pass 540 tests after locked installs with matching Windows `wetext` wheels. Chatterbox/Perth commits and the FFmpeg archive/hash are pinned; FFmpeg made a short MP4 locally. The candidate workflow has not run on a clean runner; task 3.2 remains in progress. WebUI text translated from Chinese to English in incoming edits still needs product review. Packaged GUI/media and Git persistence gates remain open.
