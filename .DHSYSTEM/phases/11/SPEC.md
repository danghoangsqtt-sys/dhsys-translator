# Phase 11 — Phụ đề động kiểu Remotion

Status: planned. Request: [ENH-009](../../requests/ENH-009.md). UI direction: `ui-direction/2026-10-22-guided-workflow/pages/captions.html`.

## Goal

Offer three animated caption styles — Karaoke từng từ, Câu nền bo góc, Song ngữ động — rendered as ASS and burned with the bundled FFmpeg/libass. No Node, Chromium or Remotion.

## Design

- New param `caption_style`: `classic` (default, current behaviour), `karaoke`, `box`, `bilingual`. `subtitle_type` enum is unchanged.
- Pure module `videotrans/util/caption_styles.py`:
  - `estimate_word_timings(text, start_ms, end_ms, lang)` — uses real word timestamps when supplied; otherwise splits the cue duration proportionally to syllable/character weight (Vietnamese syllables are space-separated).
  - `build_ass(cues, style, video_w, video_h, font)` — returns ASS text.
  - Karaoke: `{\kf<cs>}` per word with `SecondaryColour` = base and `PrimaryColour` = accent, optional `\t` scale pop.
  - Box: `BorderStyle=3` opaque box, `\fad(150,150)`.
  - Bilingual: target line animated (karaoke or box), source line smaller and static via a second style.
- Integration point: `SubtitleMixin._process_subtitles` → when `caption_style != classic`, build ASS from the final target (and source) SRT instead of `set_ass_font`, force hard-subtitle output, and also copy the `.ass` to `target_dir`.
- Timing source: target SRT cue times after alignment; word timestamps used only when the cue text is in the recognized language (no translation).
- Font: bundle Be Vietnam Pro (SIL OFL 1.1) and pass its directory to libass (`subtitles=...:fontsdir=...`) so Vietnamese diacritics never fall back.

## Compatibility contract

- `caption_style=classic` output is byte-identical to the current ASS for the same input.
- Soft subtitle selections with an animated style switch to hard subtitles, with a visible notice in Step 2.
- Existing ASS style editor (`component/set_ass.py`) keeps working for `classic`; animated styles expose only font, size, accent colour and position.

## Task order

1. [11.1](tasks/11.1.md) — caption style model, word timing and ASS builder.
2. [11.2](tasks/11.2.md) — pipeline integration and font bundling.
3. [11.3](tasks/11.3.md) — style picker UI and media acceptance.
