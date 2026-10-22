# Phase 8 summary — Provider mặc định dùng được ở Việt Nam

Status: PASS on 2026-10-22. Request: ENH-009. Product manifest remains 4.14; the independent Phase 3 clean-runner and Phase 5 clean-machine/signing gates are still open.

## Outcomes

- Default desktop lists show 11 translation, 16 recognition and 13 TTS providers: online no-key services, OpenAI/Gemini/OpenRouter accounts, local models/services and custom endpoints.
- DeepSeek, Azure GPT, DeepL, Deepgram, ElevenLabs STT/TTS and Azure TTS joined the China-hosted clouds behind **Nâng cao → Hiện tất cả nhà cung cấp**; the switch lives only in that submenu.
- A saved hidden provider stays selected and is labelled "(ẩn)" / "(hidden)"; show-all restores every row and original label.
- WebUI dropdowns list default providers first and label the rest "(Advanced)" with unchanged values; `cli.py --list providers` marks `[advanced]`; CLI examples use a Vietnamese voice.
- `scripts/audit_provider_surfaces.py` guards against new desktop provider combos that bypass the policy.
- All 29/33/38 provider IDs, credentials, saved selections and Chinese media-language support are unchanged.

## Verification

- Full Python 3.12.14 suite: 748 passed, 1 external `pydub/audioop` warning.
- Frozen candidate `dist/sp/sp.exe` SHA-256 `8193689682F8CF3E82AED4A4E50199E1114DF8E733DC5907A9BE91066B7D01B1`: core, sidebar 5/5, dynamic menus 72/72, Vietnamese and English UI probes pass, including the new provider-visibility checks. Evidence: `evidence/task-8.3-*.json`.

## Files changed

### Created

- `scripts/audit_provider_surfaces.py`
- `tests/test_provider_surfaces.py`
- `.DHSYSTEM/phases/8/evidence/`
- `.DHSYSTEM/phases/8/SUMMARY.md`

### Modified

- `videotrans/ui/provider_visibility.py`, `videotrans/ui/_setup_menus.py`
- `videotrans/language/vi_VN.json`, `videotrans/language/en_US.json`
- `webui.py`, `cli.py`
- `scripts/smoke_frozen_ui.py`
- `tests/test_provider_visibility.py`
- `README.md`, `CHANGELOG.md`
