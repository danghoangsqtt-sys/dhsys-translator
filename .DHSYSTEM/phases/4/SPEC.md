# Phase 4 localization contract — ENH-003

Status: planned on 2026-10-05. Source request: [ENH-003](../../requests/ENH-003.md), committed as `feaf5fe7`. This supplements [docs/SPEC.md](../../../docs/SPEC.md) UI-10 and does not mark Phase 4 or the Phase 3 release gate complete.

## Vietnamese-first workflow contract — ENH-004 (tasks 4.13–4.18)

### Product boundary

- Preserve the PySide6 desktop, CLI/WebUI contracts, provider numeric IDs and Chinese media-language processing.
- Make the desktop basic path task-first and free-first: local processing is functional without cloud credentials; remote profiles are explicit opt-ins.
- Hard subtitles are the default visual outcome for the main video-translation workflow. Soft subtitles and no subtitles remain supported choices with plain-language explanations.
- Edit dialogs must be accessible by mouse and keyboard, use the active light palette, and never auto-save/auto-close by default.
- VieNeu is an optional loopback pilot through the existing OpenAI-compatible TTS interface. It is not a bundled dependency or default until benchmark evidence is accepted.

### Compatibility and safety rules

- Never rewrite visible SRT merely to influence pronunciation. Pronunciation preparation is separate transient `tts_text` plus project glossary data.
- Hide/deprecate providers before deletion; saved settings need an explicit compatible path. Provider policy distinguishes local execution from remote data transfer.
- A completed ENH-004 does not close the independent Phase 3 clean-runner, provider-media or release gates.

### Acceptance matrix

| Surface | Required evidence |
| --- | --- |
| Subtitle editor | Both dialogs allow focus, selection and mouse/keyboard editing; contrast and save/skip behavior are tested. |
| Subtitle output | Hard subtitle pixels and soft subtitle stream/metadata are independently asserted; no-subtitle choice is deliberate. |
| Navigation/profile | Basic routes are task-oriented, all legacy actions remain reachable and profile changes preserve saved configuration. |
| TTS | VieNeu loopback pilot, Edge fallback, SRT preservation and pronunciation benchmark have reproducible evidence. |
| Delivery | Source and frozen Windows smoke cover the complete single-video workflow; no misleading release claim is made. |

## Product boundary

- **Interface locale:** exactly `vi_VN` and `en_US` for application-authored desktop, CLI and WebUI text. New installations retain the Vietnamese default. A deliberate old `zh_CN`/`zh` UI setting falls back to English and is migrated without changing unrelated settings.
- **Media language:** stays independent of interface locale. Recognition, translation, subtitles, TTS, provider/model/voice catalogs and input/output language choices continue to support Chinese (`zh`, `zh-cn`, `zh-tw`, Cantonese where present). Chinese words in user media, provider data and model/voice identifiers are data, not UI locale text.
- **Frozen application:** must not select Chinese UI even if an older user-data directory still contains `videotrans/language/zh_CN.json`; the supported locale list must be explicit rather than inferred solely from available JSON files.
- **Compatibility:** keep existing task, output and API contracts. If a control was previously gated by `defaulelang == 'zh_CN'`, decide its visibility by feature availability or settings, not by leaving it inaccessible.

## Acceptance matrix

| Surface | Required evidence |
| --- | --- |
| Locale choice | Desktop selector, splash and packaged UI offer Vietnamese/English only; aliases, environment flags and saved old locale migrate predictably. |
| App-authored text | Task summaries, status, errors, menus, dialogs, CLI and WebUI show Vietnamese or English with no Chinese fallback. |
| Chinese media | `zh`/`zh-cn`/`zh-tw` remain in content-language choices and representative recognition → translation → subtitle/TTS flow retains Chinese support. |
| Regression | Focused behavior tests, full supported Python 3.12 suite, offscreen desktop smoke and frozen Windows smoke pass; Phase 3 clean-runner/provider gates remain separate. |

## Task order

1. [4.9](tasks/4.9.md) — explicit UI locale policy and old-setting migration.
2. [4.10](tasks/4.10.md) — application-authored runtime messages and bilingual catalogs.
3. [4.11](tasks/4.11.md) — CLI/WebUI localization and content-language separation.
4. [4.12](tasks/4.12.md) — packaged regression, real media check and documentation.

Existing uncommitted changes to `videotrans/task/taskcfg.py`, `videotrans/component/clip_video.py` and language JSON files must be reviewed before implementation. Preserve them and adapt tasks to their current state.
