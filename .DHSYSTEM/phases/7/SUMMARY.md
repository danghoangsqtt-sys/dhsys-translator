# Phase 7 summary — Việt Nam/global provider visibility and free-first guidance

Status: PASS locally on 2026-10-07. Request: ENH-007. Product manifest remains 4.14 because the independent clean-runner, clean-machine and signing gates are still open.

## Outcomes

- Preserved all 29 translation, 33 recognition and 38 TTS provider IDs, modules, saved selections and credentials.
- Added one curated Viet Nam/global view across main and quick-tool combo boxes plus provider settings menus.
- Added a persisted **Show all providers** action that restores every advanced/China-focused/less-common integration.
- Added a recommended no-API-key profile using faster-whisper, Google translation and Edge-TTS.
- Replaced ambiguous “Built-in” wording with local-model-download guidance and added tooltips for local, online-no-key, provider-API, local-service and custom-endpoint categories.
- Updated Vietnamese/English documentation and regenerated the sanitized README workspace screenshot.

## Verification

- Focused provider/profile/config/menu/workspace/responsive suite: 75 passed.
- Full Python 3.12.14 suite: 726 passed, 1 external `pydub/audioop` deprecation warning.
- Both locale catalogs pass `json.tool`; `compileall` and `git diff --check` pass.
- The regenerated workspace screenshot was visually inspected and shows the no-key recommendation and best-effort disclosure.

## Files changed

### Created

- `videotrans/ui/provider_visibility.py`
- `tests/test_provider_visibility.py`
- `.DHSYSTEM/phases/7/SUMMARY.md`

### Modified

- `.DHSYSTEM/HANDOFF.json`
- `.DHSYSTEM/ROADMAP.md`
- `.DHSYSTEM/TRACKER.md`
- `.DHSYSTEM/phases/7/PHASE-STATE.md`
- `.DHSYSTEM/phases/7/tasks/7.1.md`
- `.DHSYSTEM/phases/7/tasks/7.2.md`
- `.DHSYSTEM/phases/7/tasks/7.3.md`
- `CHANGELOG.md`
- `README.md`
- `docs/assets/readme/workspace-vi.png`
- `docs/huong-dan-test-va-su-dung.md`
- `scripts/capture_readme_screenshots.py`
- `tests/test_app_params.py`
- `tests/test_light_workspace.py`
- `tests/test_provider_profiles.py`
- `videotrans/configure/_app_params.py`
- `videotrans/language/en_US.json`
- `videotrans/language/vi_VN.json`
- `videotrans/mainwin/main_win.py`
- `videotrans/ui/_setup_menus.py`
- `videotrans/ui/fn_peiyin.py`
- `videotrans/ui/fn_peiyinrole.py`
- `videotrans/ui/provider_profiles.py`
- `videotrans/ui/workspace_shell.py`
- `videotrans/winform/fn_fanyisrt.py`
- `videotrans/winform/fn_peiyin.py`
- `videotrans/winform/fn_peiyinrole.py`
- `videotrans/winform/fn_recogn.py`

## Open release gates

- Phase 3 GitHub clean-runner/release gate.
- Phase 5 clean Windows recipient, shortcuts, SmartScreen and Authenticode signing evidence.
