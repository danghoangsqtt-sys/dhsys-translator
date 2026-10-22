# Phase 10 — Wizard 3 bước

Status: planned. Request: [ENH-009](../../requests/ENH-009.md). UI direction: `ui-direction/2026-10-22-guided-workflow/pages/step1-video.html`, `step2-options.html`, `step3-result.html`.

## Goal

The app opens on a three-step guided flow — Chọn video → Ngôn ngữ, giọng & phụ đề → Chạy & xem kết quả — with technical options folded into "Nâng cao". A persisted toggle returns to the classic workspace.

## Design

- `GuidedWizard` (`videotrans/ui/wizard/`) is a `QStackedWidget` of three pages hosted by `WorkspaceShell` as a new default route.
- The wizard writes the same params the classic workspace writes (`source_language`, `target_language`, `tts_type`, `voice_role`, `subtitle_type`, `recogn_type`, `translate_type`, …) and starts jobs through the existing `win_action.check_start` path; no new pipeline.
- Step 1 accepts drag-and-drop or a file chooser for one or many videos (existing batch path) and a purpose preset: Lồng tiếng + phụ đề / Chỉ phụ đề / Chỉ SRT.
- Step 2 shows language selectors, voice tiles with "Nghe thử" (existing `util/ListenVoice.py`), caption style tiles (Phase 11 adds the animated ones), a summary with cost category from `provider_visibility` and a rough time estimate, and a collapsible "Nâng cao" section that hosts the existing controls.
- Step 3 shows per-stage progress from `workflow_state` and embeds `ResultPanel` (Phase 9); batches show a per-video list.
- `ui_mode` param: `wizard` (default for new installs and upgrades) or `classic`; switching never resets other params.

## Compatibility contract

- Classic workspace, sidebar tools, menus and 72 dynamic routes stay intact.
- No widget owns media logic; presets only set existing params.
- Vietnamese and English UI only; Chinese media languages remain selectable.

## Task order

1. [10.1](tasks/10.1.md) — wizard shell, routing and `ui_mode` toggle.
2. [10.2](tasks/10.2.md) — Step 1 and Step 2 pages.
3. [10.3](tasks/10.3.md) — Step 3 progress and batch results.
4. [10.4](tasks/10.4.md) — label review and frozen UI acceptance.
