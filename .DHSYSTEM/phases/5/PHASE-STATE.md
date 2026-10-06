# Phase 5 state — Local Windows distribution and system readiness

State: in_progress. Request: ENH-005. Tasks 5.1–5.4 are PASS locally; Task 5.5 target-machine acceptance is next while Phase 3 task 3.3 remains independently open for its deferred GitHub runner gate.

| Task | State | Gate |
| --- | --- | --- |
| 5.1 Readiness model and probes | PASS | 11 focused, 51 related and 670 full Python 3.12 tests pass; `$vp-audit` edge-case repairs verified |
| 5.2 “Kiểm tra máy” UI | PASS | 5 focused, 53 related and 675 full Python 3.12 tests; frozen Việt/Anh UI and 72/72 dynamic-menu smoke pass; sanitized read-only copy/export verified |
| 5.3 Consent-based remediation | PASS | 18 focused, 29 readiness/remediation/UI, 17 provider-profile regression and 688 full Python 3.12 tests pass; `$vp-audit` HTTPS/state repairs verified |
| 5.4 Portable ZIP and Setup.exe | PASS | One-command local build + auto verification PASS; 11,291-file / 6.16 GiB candidate, ZIP/Setup/manifest hashes recorded, 14 focused + 702 full Python 3.12 tests pass |
| 5.5 Target-machine acceptance | not_started | Portable/install/upgrade/uninstall/media/diagnostic evidence and recipient guide |

Product constraints: preserve provider/model IDs and persisted enums, Chinese media-language support, user SRT fidelity and user-data paths. GitHub is not required for this phase.
