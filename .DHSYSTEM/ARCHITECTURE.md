# Architecture — Vietnamese-first workflow extension

## DHSYSTEM organization context

No organization profile is configured. The architecture preserves upstream licensing and project identity metadata.

## System overview

ENH-004 is an incremental layer over the current PySide6 task pipeline. It changes presentation defaults and adds reversible configuration/profile and TTS-text preparation boundaries. It does not replace recognition, translation, TTS or FFmpeg assembly implementations.

```mermaid
flowchart LR
    User[Desktop user] --> Shell[WorkspaceShell / basic task UI]
    Shell --> Profiles[Provider profile resolver]
    Profiles --> Params[Existing params and provider registries]
    Params --> Pipeline[Existing single-video task pipeline]
    Pipeline --> STT[Recognition providers]
    Pipeline --> TR[Translation providers]
    Pipeline --> Prep[TTS text preparation + glossary]
    Prep --> TTS[Existing TTS adapters]
    Pipeline --> Edit[Subtitle correction dialogs]
    Pipeline --> FFmpeg[Subtitle and media assembly]
    FFmpeg --> Output[Video + SRT + output receipt]
```

## Data flow

```mermaid
flowchart TD
    Media[Input media] --> Recognize[STT]
    Recognize --> SourceSRT[Source SRT]
    SourceSRT --> Correct[User correction]
    Correct --> Translate[Translation]
    Translate --> TargetSRT[Target SRT: display source of truth]
    TargetSRT --> Pronounce[Language spans + project glossary]
    Pronounce --> TTSText[Transient tts_text]
    TTSText --> Synthesize[TTS]
    TargetSRT --> SubtitleMode{Subtitle mode}
    SubtitleMode -->|Hard| Burn[Burn into video pixels]
    SubtitleMode -->|Soft| Mux[Mux subtitle stream]
    SubtitleMode -->|None| NoSub[Explicit no-subtitle output]
    Synthesize --> Assemble[FFmpeg assembly]
    Burn --> Assemble
    Mux --> Assemble
    NoSub --> Assemble
```

## Component decisions

| Component | Decision | Rationale |
| --- | --- | --- |
| Subtitle editor | Repair current `QTableWidget` dialogs | Lowest-risk fix; current data contracts already exist |
| Provider profiles | Mapping layer over current registries/params | Avoids persisted enum breakage and keeps advanced providers reachable |
| TTS pronunciation | Separate `tts_text` preparation service | Protects subtitle fidelity and makes glossary behavior testable |
| VieNeu | External loopback OpenAI-compatible pilot | Avoids dependency conflicts and keeps packaging unchanged during evaluation |
| Subtitle default | Hard subtitle for fresh main workflow | Matches user expectation that captions are immediately visible |
| Provider removal | Deferred until audit/migration task 4.17 | Prevents configuration loss and unsupported assumptions about local models |

## Diagram applicability matrix

| Diagram | Status | Rationale |
| --- | --- | --- |
| system-overview | required | ENH-004 affects UI, profiles and three processing stages |
| data-flow | required | Visible SRT and transient TTS text must remain separate |
| event-flows | optional | Dialog events are sufficiently specified in task 4.13 |
| module-dependencies | optional | Detailed imports belong to implementation design |
| deployment | required for Phase 5 | Portable/installer boundaries, writable user data and consent-based remediation must remain explicit |
| user-use-case | N/A | User outcomes are captured in PROJECT-CONTEXT |

## Deployment and runtime

The packaged app remains a Windows onedir PyInstaller application. VieNeu runs as an optional local companion process on loopback during the pilot. Gemini/OpenRouter-compatible profiles are outbound API integrations and must remain optional.

ENH-005 adds two local distribution wrappers around the same verified onedir tree: a portable ZIP and a per-user Windows installer. Required application runtime assets remain bundled; writable settings/models/logs/output remain outside the install tree. A pure readiness service feeds a localized UI and a separate allowlisted remediation coordinator. The scanner never owns provider selection or media processing.

```mermaid
flowchart TD
    Build[Tracked local build script] --> Frozen[Verified PyInstaller onedir]
    Frozen --> Zip[Portable ZIP + SHA-256]
    Frozen --> Setup[Per-user Setup.exe + SHA-256]
    Zip --> App[Desktop application]
    Setup --> App
    App --> Scan[Read-only readiness probes]
    Scan --> Report[Workload-specific status + sanitized report]
    Report --> Fix{User explicitly chooses a fix?}
    Fix -->|No| Guide[Guidance / CPU fallback]
    Fix -->|Yes| Allowlist[Allowlisted remediation coordinator]
    Allowlist --> Rescan[Post-check and rescan]
```

## Open architecture questions

- Exact persisted schema for provider profiles and project glossary.
- Whether code-switch detection should be deterministic-only in Phase 4.16 or optionally LLM-assisted after a privacy review.
- How long English spans must be before dual-voice synthesis is offered.
- Which prerequisite checks are actually required by the final frozen candidate versus merely recommended for optional GPU/local-model workloads.
- Whether code signing is available for locally shared Setup/portable artifacts; unsigned builds must document Windows SmartScreen expectations truthfully.
