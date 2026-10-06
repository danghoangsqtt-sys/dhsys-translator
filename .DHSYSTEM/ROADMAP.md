# Roadmap

## Planned extension — ENH-004 Vietnamese-first video workflow

Phase 4 tasks 4.13–4.18 are complete and persisted. Their order was deliberate: repair subtitle correction first, prove hard/soft subtitle output second, simplify navigation/provider choice third, then pilot Vietnamese–English TTS before any provider reduction decision.

| Task | Outcome | State |
| --- | --- | --- |
| 4.13 | Subtitle editor is readable and editable by mouse/keyboard; no default auto-close | PASS |
| 4.14 | Hard/soft/no-subtitle output is explicit and independently verified | PASS |
| 4.15 | Task-first sidebar and three reversible provider profiles | PASS |
| 4.16 | Local VieNeu pilot plus non-destructive En–Vi pronunciation glossary | PASS |
| 4.17 | Provider migration/deprecation policy based on access, privacy and evidence | PASS |
| 4.18 | Source and frozen Windows end-to-end acceptance plus user documentation | PASS |

Source: `docs/brainstorm/session-2026-10-05-vietnamese-first-video-workflow.md`. Contracts: `.DHSYSTEM/phases/4/tasks/4.13.md` through `4.18.md`. This extension does not close the independent Phase 3 release gates and does not authorize provider deletion.

Source: `docs/PLAN.md` and `docs/SPEC.md`. Status is recorded here after each phase.

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | Reproducible tests, stale tests, version and docs | verified locally; git persistence pending |
| 2 | ASR parsing, TLS, WebUI access, output safety | verified locally; git persistence pending |
| 3 | Audit repair queue 3.4–3.9, supported Python, dependencies, Windows packaging and release gate | in_progress; source, Docker, extracted Windows and current-candidate provider media locally verified; clean-runner/release gate open |
| 4 | PySide6 workflow UI, light workspace layout, ENH-003 Vietnamese/English UI locales with Chinese media support | complete; tasks 4.1–4.18 persisted; Phase 3 release gate remains independent and open |
| 5 | ENH-005 local Windows distribution, machine readiness scan and consent-based setup assistant | in_progress; tasks 5.1–5.2 PASS locally; GitHub-independent |
| 6 | Timeline editor | conditional; scope decision pending |

ENH-003 is added to Phase 4. ENH-005 is active in [Phase 5](phases/5/SPEC.md) so the owner can build and share portable/installer artifacts directly without GitHub. Target product version after the pending 4.14.1 repair line: **4.15.0 (provisional)**. Phase 5 progress does not change the current `4.14` manifest or publish an artifact.

## Phase 5 — Local distribution and machine readiness

| Task | Outcome | State |
| --- | --- | --- |
| 5.1 | Pure readiness model and Windows hardware/runtime probes | PASS locally |
| 5.2 | Việt/Anh “Kiểm tra máy” UI and sanitized support report | PASS locally |
| 5.3 | Explicit, allowlisted remediation assistant | next |
| 5.4 | Local portable ZIP and Setup.exe build pipeline | planned |
| 5.5 | Recipient-style Windows acceptance and user handoff | planned |

Source: [ENH-005](requests/ENH-005.md). GitHub is not required. The phase preserves all provider/model IDs, saved subtitle/provider mappings, Chinese media-language support and the separation between displayed SRT and transient TTS pronunciation text.
