# Roadmap

Source: `docs/PLAN.md` and `docs/SPEC.md`. Status is recorded here after each phase.

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | Reproducible tests, stale tests, version and docs | verified locally; git persistence pending |
| 2 | ASR parsing, TLS, WebUI access, output safety | verified locally; git persistence pending |
| 3 | Audit repair queue 3.4–3.9, supported Python, dependencies, Windows packaging and release gate | in_progress; source, Docker and extracted Windows smoke locally verified; clean-runner/release/persistence gates open |
| 4 | PySide6 workflow UI, light workspace layout, ENH-003 Vietnamese/English UI locales with Chinese media support | in_progress; 4.1–4.10 verified locally; 4.11–4.12 planned; Phase 3 release gates remain open |
| 5 | Timeline editor | conditional; scope decision pending |

ENH-003 is added to the current Phase 4. Target product version after the pending 4.14.1 repair release: **4.15.0 (provisional)**. Planning does not change the current `4.14` manifest or publish an artifact. See [Phase 4 localization contract](phases/4/SPEC.md).
