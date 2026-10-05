# System rules for ENH-004

## Compatibility

- Preserve numeric provider IDs and existing saved settings until a tested migration exists.
- Preserve GUI, CLI, WebUI and media-language behavior unless the active task explicitly changes them.
- Keep Chinese media processing independent from the Vietnamese/English UI locale policy.
- Do not place provider or media-processing decisions inside presentation widgets.

## Subtitle integrity

- Treat the displayed SRT as user content and the source of truth for captions.
- Generate TTS-specific text in a separate transient structure; never overwrite SRT for pronunciation.
- Test `Save and continue` and `Continue without saving` as different data contracts.
- Verify hard subtitles by decoded visual evidence and soft subtitles by stream/metadata inspection.

## UI quality

- Editable tables must allow focus, selection, keyboard traversal and visible editing state.
- Use the shared light palette; avoid dialog-local colors that reduce contrast.
- Destructive/cancel/no-save actions must be visually and verbally distinct from the primary save action.
- No timer may auto-save or close an editing dialog by default.

## Provider and privacy rules

- Profiles are named by outcome and data path, not by a promise of unlimited free service.
- Loopback services bind to `127.0.0.1` by default.
- Never log API keys, reference audio, full private paths or sensitive provider responses.
- Deprecate/hide before deletion; document every migration and fallback.

## Quality gates

- Run focused tests for the active task before the full supported Python suite.
- UI work requires offscreen Qt smoke at relevant sizes and both Vietnamese/English locales.
- Media output work requires a short deterministic fixture plus `ffprobe`/decoded-frame evidence.
- Frozen Windows verification is required in task 4.18; it does not replace Phase 3 clean-runner gates.
