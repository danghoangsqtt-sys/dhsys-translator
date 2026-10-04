# Tracker

- Current phase: 3 — supported runtime and Windows packaging
- Current task: 3.3 — release gate and documentation; 3.6 artifact gates remain open
- State: 3.4–3.5, 3.7–3.9 and 3.1 verified locally; 3.2, 3.6 and 3.3 in_progress; phases 1–2 verified locally; local Git checkpoint exists but upstream persistence is pending
- Local branch/checkpoint: `codex/phase3-release-gate` at `fbcd924f` for the prior Phase 1–3 changes; no upstream is configured for this branch
- Planned patch version: 4.14.1 (not yet applied to product manifest)
- Starting commit: `8cf344fe`
- Input artifacts: `docs/PLAN.md`, `docs/SPEC.md`, `docs/BUGFIX-PLAN.md`, `.DHSYSTEM/audit-report.md`, `.DHSYSTEM/requests/`, `docs/brainstorm/session-2026-10-03.md`

## Evidence

- Continuation on 2026-10-04: Python 3.12.13 full suite 540 passed; Docker image rebuilt from the current workspace and host-port/auth probe returned 401 without login, 200 with valid login, 401 with wrong credentials. Network bind without credentials exits with an error. Packaged script probe on the older Python 3.12 artifact exposed missing `jaraco.text` in `pkg_resources` before app startup; task 3.2 remains in progress while `sp.spec` is corrected and rebuilt.

- Task 3.3 on 2026-10-04: runtime documentation and state records reconciled. The Python 3.12 artifact starts twice headlessly with temporary user data and staged FFmpeg. Focused release-path suite: 97 passed; lock/YAML/diff checks pass. Docker daemon is unavailable, and clean-runner, packaged provider/media, checksum and Git persistence gates remain open.

- Task 3.2 on 2026-10-04: Python 3.12 PyInstaller creates the onedir artifact and it starts headlessly; resources and staged FFmpeg layout verified. Python 3.10 crashes in the torchaudio hook, so the candidate workflow now uses tested 3.12. Clean runner, packaged dynamic provider, and media smoke remain open.

- Task 3.1 on 2026-10-04: locked Python 3.10.19, 3.11.15, 3.12.13 environments with `wetext` each pass 540 tests; CLI and offscreen GUI import pass. FFmpeg pinned archive SHA-256 matches and short MP4 has audio/video. Chatterbox/Perth are pinned to commits; `uv lock --check --offline` passes (424 packages). Audit/debug repaired invalid escape warnings and isolated a test harness pipe exit. Clean Windows artifact and Git persistence gates remain open.

- Task 3.9 on 2026-10-04: saved language codes resolve to valid WebUI dropdown choices and voice roles; desktop short locale flags are parsed before config import. Qt/CLI tests now invoke product behavior. Focused 102/full Python 3.10 540 tests pass. Audit/debug removed a trailing blank line; Git persistence and packaged media smoke remain open.

- Task 3.8 on 2026-10-04: global Hugging Face monkeypatch removed; model cache/downloads validate size/hash and reject one-byte model files. Local HTTP artifact/reuse and concurrent callback probes pass. Focused 7/full Python 3.10 546 tests pass. Audit/debug closed a one-byte matching-Length gap. Git persistence remains open.

- Task 3.7 on 2026-10-04: valid CA preserved, invalid CA rejected with named setting; only app-descendant FFmpeg terminated. Live probe left unrelated PID 17904 running while owned process stopped, then cleaned up probe. Focused 7/full 539 Python 3.10 tests pass. Audit found no new task-scope failure; Git persistence and packaged GUI smoke remain open.

- Task 3.6 on 2026-10-04: 534 Python 3.10 tests pass, frozen import from another CWD leaves install tree untouched, Docker entry/auth contract is covered. Audit/debug repaired missing user-data directory and filename-loaded FunASR helper path. Docker image build restarted with webui-only extra; real container and extracted Windows artifact smoke are pending, so task stays in_progress.

- Task 3.5 on 2026-10-04: shared guarded cache cleanup, unique CLI run directories and per-run cache; 88 focused/528 full Python 3.10 tests passed. Audit found no new task-scope failure, so no debug repair was needed. Git persistence remains open.

- Task 3.4 on 2026-10-04: legacy config regression tests 5 passed, full Python 3.10 suite 523 passed, scratch Docker context image excluded dummy environment secret and local params/cfg files. Audit found no remaining task 3.4 product failure; debug fixed a test-only missing dependency. Git persistence remains open, so no PASS/release claim.

- Audit repair planning 2026-10-04: 15 BUG and 1 ENH request mapped to Phase 3 tasks 3.4–3.9, 3.1–3.3. No audit finding is marked fixed by this planning update. The queue and G3a–G3c release criteria are in `docs/BUGFIX-PLAN.md`.

- Initial audit host had Python 3.14.0 and 3.12.13 while the original manifest pinned 3.10; later local manifest now allows 3.10–3.12, with optional `wetext` still constrained to cp310 on Windows.
- Prior host run: 4 test collection errors; a focused subset had 39 passing and 3 failing tests on Python 3.14.
- Python 3.10.19 environment installed; `uv lock --check` passed and 394 packages installed.
- Full collection: 3 stale imports. Excluding those files: 416 tests passed, 60 failed, 0 setup errors with a workspace basetemp.
- Task 1.1 is locally verified; git persistence is pending, so it is not marked PASS.
- All 488 collected tests now pass on Python 3.10.19; the only warning is FFmpeg absent from the current PATH. CLI `--version` reports 4.14 and install docs match the `webui` extra.
- Existing provider index numbers changed before this work while the UI persists `translate_type` as a number. This needs a migration decision before public upgrade; current numbers are frozen by tests.
- VibeVoice parser no longer evaluates response text. Eleven focused parser tests and the full 499-test suite pass.
- Removed hardcoded TLS bypasses from 16 modules. A static certificate-verification policy test and an HTTPS adapter test pass.
- WebUI now defaults to loopback, requires authentication for network/share mode, and excludes logs/config/old files from downloads. Full suite: 512 passed.
- Cache cleanup now rejects paths outside the managed temp root, WebUI preserves prior runs, and `only_out_mp4` keeps prior exports on collision. Full suite: 517 passed.
- Review on 2026-10-04: Nemotron's runtime manifest supports 3.10–3.12; isolated Python 3.12 core install and 518 tests passed. Python 3.10 also passes 518 tests. `wetext` fails on Python 3.12 because its Windows Pynini wheel is cp310. The initial packaging workflow referenced ignored `sp.spec`, expected an onedir path from a onefile spec, and attempted automatic release; those static defects are corrected locally. A real CLI `--help` crash and lost Chinese CLI messages were corrected with a regression test. Candidate runner build and packaged smoke are still required. The incoming WebUI English translation needs product review. Fresh offline lock verification is blocked by the existing mutable Chatterbox source URL.
