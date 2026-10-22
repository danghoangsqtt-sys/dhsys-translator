# Phase 9 — Màn hình kết quả có trình phát

Status: complete (2026-10-22). Request: [ENH-009](../../requests/ENH-009.md). UI direction: `ui-direction/2026-10-22-guided-workflow/pages/step3-result.html`.

## Goal

When a translation job finishes, the user watches the output inside the app, compares it with the original, and can open the folder, open an external player, fix subtitles and re-export, or start another video.

## Design

- A reusable `ResultPanel` widget (`videotrans/ui/result_panel.py`) is driven only by the existing `output_receipt` payload (`video_path`, `subtitle_paths`, `subtitle_type`, …); it never reads task internals.
- Playback uses `QMediaPlayer` + `QAudioOutput` + `QVideoWidget`, the same stack already used in `component/onlyone_set_editdubb.py` and collected by `sp.spec`.
- Soft-subtitle outputs show the selected SRT as an overlay label synced to `positionChanged`; hard-subtitle outputs need no overlay.
- Modes: Bản dịch (output), Gốc (input), Cạnh nhau (two players with a shared position).
- "Sửa phụ đề & xuất lại" opens the existing subtitle editor (task 4.13) and re-runs only the assemble stage into a new non-overwriting file.
- Recent results are stored as receipts in a small JSON list under the user data directory (max 20, paths only, no media).

## Compatibility contract

- `format_output_receipt` and the receipt JSON stay backward compatible; new fields are optional.
- The classic workspace keeps its current text receipt; the panel is additive.
- A missing or moved output file shows a clear message instead of an empty player.

## Task order

1. [9.1](tasks/9.1.md) — `ResultPanel` with playback, file list and actions.
2. [9.2](tasks/9.2.md) — compare modes, soft-subtitle overlay, re-export and history.
3. [9.3](tasks/9.3.md) — frozen playback acceptance.
