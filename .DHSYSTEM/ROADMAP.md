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
| 5 | ENH-005 local Windows distribution, machine readiness scan and consent-based setup assistant | in_progress; tasks 5.1–5.4 PASS locally; GitHub-independent |
| 6 | Timeline editor | conditional; scope decision pending |
| 7 | ENH-007 Việt Nam/global provider visibility and free-first guidance | complete; reversible curated view, no-key profile and bilingual cost guidance; 726 tests pass |
| 8 | ENH-009 default providers usable in Viet Nam; China-hosted and less-common clouds under Advanced | complete; 8.1–8.3 PASS; frozen candidate verified |
| 9 | ENH-009 result screen with in-app playback, compare, re-export and history | complete; 9.1–9.3 PASS; frozen playback verified |
| 10 | ENH-009 three-step guided wizard (default) with classic toggle and batch queue | in_progress; 10.1 PASS |
| 11 | ENH-009 animated captions (karaoke, rounded box, bilingual) via ASS + FFmpeg | planned |

ENH-003 is added to Phase 4. ENH-005 is active in [Phase 5](phases/5/SPEC.md) so the owner can build and share portable/installer artifacts directly without GitHub. Target product version after the pending 4.14.1 repair line: **4.15.0 (provisional)**. Phase 5 progress does not change the current `4.14` manifest or publish an artifact.

## Phase 5 — Local distribution and machine readiness

| Task | Outcome | State |
| --- | --- | --- |
| 5.1 | Pure readiness model and Windows hardware/runtime probes | PASS locally |
| 5.2 | Việt/Anh “Kiểm tra máy” UI and sanitized support report | PASS locally |
| 5.3 | Explicit, allowlisted remediation assistant | PASS locally |
| 5.4 | Local portable ZIP and Setup.exe build pipeline | PASS locally |
| 5.5 | Recipient-style Windows acceptance and user handoff | in_progress |

Source: [ENH-005](requests/ENH-005.md). GitHub is not required. The phase preserves all provider/model IDs, saved subtitle/provider mappings, Chinese media-language support and the separation between displayed SRT and transient TTS pronunciation text.

## Phase 7 — Provider Việt Nam/quốc tế và free-first guidance

| Task | Outcome | State |
| --- | --- | --- |
| 7.1 | Central provider visibility/cost policy with frozen registry compatibility | PASS |
| 7.2 | Filtered desktop surfaces, show-all control and no-key recommended profile | PASS |
| 7.3 | Việt/Anh cost guidance, docs and regression acceptance | PASS |

Source: [ENH-007](requests/ENH-007.md). This phase hides only presentation rows/actions; it does not delete providers, renumber saved indexes or remove Chinese media-language support.

## Phases 8–11 — ENH-009 guided workflow, result review and animated captions

Order is deliberate: provider cleanup first, then result review (needed by the wizard's last step), then the wizard, then animated captions.

### Phase 8 — Provider mặc định dùng được ở Việt Nam ([SPEC](phases/8/SPEC.md))

| Task | Outcome | State |
| --- | --- | --- |
| 8.1 | Narrow curated provider policy | PASS |
| 8.2 | Close provider visibility leaks | PASS |
| 8.3 | Frozen rebuild and acceptance | PASS |

### Phase 9 — Màn hình kết quả có trình phát ([SPEC](phases/9/SPEC.md))

| Task | Outcome | State |
| --- | --- | --- |
| 9.1 | ResultPanel with in-app playback | PASS |
| 9.2 | Compare modes, re-export and history | PASS |
| 9.3 | Frozen playback acceptance | PASS |

### Phase 10 — Wizard 3 bước ([SPEC](phases/10/SPEC.md))

| Task | Outcome | State |
| --- | --- | --- |
| 10.1 | Wizard shell and classic toggle | PASS |
| 10.2 | Step 1 and Step 2 pages | planned |
| 10.3 | Step 3 progress and batch results | planned |
| 10.4 | Label review and frozen UI acceptance | planned |

### Phase 11 — Phụ đề động kiểu Remotion ([SPEC](phases/11/SPEC.md))

| Task | Outcome | State |
| --- | --- | --- |
| 11.1 | Caption styles, word timing and ASS builder | planned |
| 11.2 | Pipeline integration and font bundling | planned |
| 11.3 | Caption style picker and acceptance | planned |

Source: [ENH-009](requests/ENH-009.md). Hiding stays presentation-only; `subtitle_type`, provider IDs and Chinese media-language support are preserved; no Node/Remotion dependency.
