<!-- crystallize_version: 0.8.0 -->
# Project context — Vietnamese-first video workflow

## DHSYSTEM active profile (FEAT-009)

No organization profile is bound. Public organization and personal developer fields remain unspecified.

<product_vision>

### Product scope

Provide a Vietnamese-first desktop workflow that turns a video into a translated/dubbed result with understandable defaults, editable subtitles and verifiable subtitle output. The default experience favors local/free processing; cloud services are optional profiles with explicit quota and privacy implications.

### Phase overview

- Phase 1–3: existing stability, security, runtime, packaging and release gates.
- Phase 4.1–4.12: existing light desktop workspace and Vietnamese/English UI localization.
- Phase 4.13–4.18: ENH-004 subtitle correction, subtitle output, provider profiles, VieNeu pilot, controlled provider reduction and end-to-end handoff.
- Phase 5: conditional timeline editor; not activated by ENH-004.

### Anti-goals

- No mass deletion of providers or models before migration and regression evidence.
- No removal of Chinese as a media input/output language.
- No bundled VieNeu dependency until the isolated pilot passes agreed benchmarks.
- No rewriting visible SRT into phonetic spellings for TTS.
- No promise that a free cloud quota is unlimited or production-stable.
- No Phase 3 release claim based only on Phase 4 UI tests.

</product_vision>

## User outcomes

1. A new user can finish one translated video without navigating provider-specific configuration dialogs.
2. Subtitle text can be corrected with normal mouse and keyboard behavior.
3. The output screen explains whether subtitles are burned in, toggleable, or absent.
4. Vietnamese TTS can pronounce common English technical terms predictably without altering the displayed subtitle.
5. A privacy-conscious user can run the local profile after installing the required models.

## Business and product rules

- “Free” means no mandatory paid account; it does not mean unlimited quota, zero hardware cost or guaranteed uptime.
- Provider profiles are reversible presets over existing stable provider IDs.
- Remote profiles disclose that text/audio may leave the device.
- Basic UI contains media tasks; provider configuration belongs to Settings/Advanced.
- Hard subtitles are the fresh-install default for the main video workflow. Existing saved user choice is migrated deliberately, never silently reinterpreted.

## Open decisions

- Whether the future removal policy targets only inaccessible China-hosted APIs or also local open models originating in China.
- Representative VieNeu test hardware, voices and acceptance thresholds.
- Whether profile state belongs in existing `params`, a versioned profile block, or a dedicated settings model after code-level design review.
