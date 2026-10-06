# Phase 5 state — Local Windows distribution and system readiness

State: in_progress. Request: ENH-005. Task 5.1 is PASS locally; Task 5.2 is next while Phase 3 task 3.3 remains independently open for its deferred GitHub runner gate.

| Task | State | Gate |
| --- | --- | --- |
| 5.1 Readiness model and probes | PASS | 11 focused, 51 related and 670 full Python 3.12 tests pass; `$vp-audit` edge-case repairs verified |
| 5.2 “Kiểm tra máy” UI | not_started | Việt/Anh UI, workload ratings, sanitized export, frozen smoke |
| 5.3 Consent-based remediation | not_started | Exact allowlist, explicit confirmation, safe cancellation/failure/elevation handling |
| 5.4 Portable ZIP and Setup.exe | not_started | Local reproducible build, checksum, no Python requirement, no secrets/models/user data |
| 5.5 Target-machine acceptance | not_started | Portable/install/upgrade/uninstall/media/diagnostic evidence and recipient guide |

Product constraints: preserve provider/model IDs and persisted enums, Chinese media-language support, user SRT fidelity and user-data paths. GitHub is not required for this phase.
