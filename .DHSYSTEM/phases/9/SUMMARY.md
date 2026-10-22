# Phase 9 summary — Màn hình kết quả có trình phát

Status: PASS on 2026-10-22. Request: ENH-009. Product manifest remains 4.14; the independent Phase 3 clean-runner and Phase 5 clean-machine/signing gates are still open.

## Outcomes

- Finished jobs open a non-modal **Kết quả / Result** window instead of the text-only receipt box: in-app playback (play/pause, seek, volume, fullscreen, Space and arrow keys), output files with sizes and missing-file state, Open folder, Open in another player and Translate another video.
- **Bản dịch / Gốc / Cạnh nhau** views keep the playback position; side-by-side shows the muted original following the translated video.
- Soft-subtitle outputs show the current cue(s) in a caption strip under the video.
- Up to 20 recent results are kept in `<user data>/videotrans/result_history.json` (paths and language codes only, atomic writes, gitignored) and listed after the current results.
- **Sửa phụ đề & xuất lại** edits subtitle text only and rebuilds the video into a new `-N` file from the original video and dubbed audio on a worker thread; it is disabled when the job slowed the video down.
- Receipts gained optional fields (`audio_paths`, `target_dir`, `source_video`, `source_sub`, `target_sub`, language codes, `output_srt`, `video_autorate`); older receipts still load.

## Verification

- Full Python 3.12.14 suite: 785 passed, 1 external `pydub/audioop` warning.
- Frozen candidate `dist/sp/sp.exe` SHA-256 `69A2B66EDCD11649DCBB8C0ABC95ADD68C31AAA586D3F8731B3E8AA088152F44`: core, sidebar 5/5, dynamic menus 72/72 and Vietnamese/English UI probes pass; the UI probe now plays hard- and soft-subtitle MP4s in the packaged result panel, checks the caption strip and compare modes, and runs a real re-export with the bundled FFmpeg. Evidence: `evidence/task-9.3-*.json`.

## Deviations

- Re-export rebuilds from persistent files instead of the task cache, which `set_end` deletes after success.
- Subtitle editing uses a result-only text editor because the existing editors are bound to a running job.

## Files changed

### Created

- `videotrans/ui/result_panel.py`, `videotrans/ui/result_history.py`, `videotrans/ui/result_subtitle_editor.py`
- `videotrans/task/reexport.py`
- `tests/test_result_panel.py`, `tests/test_result_history.py`, `tests/test_reexport.py`
- `.DHSYSTEM/phases/9/evidence/`, `.DHSYSTEM/phases/9/SUMMARY.md`

### Modified

- `videotrans/task/subtitle_output.py`, `videotrans/mainwin/_actions_task.py`, `videotrans/mainwin/_actions_base.py`
- `videotrans/language/vi_VN.json`, `videotrans/language/en_US.json`
- `scripts/smoke_frozen_ui.py`, `tests/test_subtitle_output.py`
- `.gitignore`, `CHANGELOG.md`
