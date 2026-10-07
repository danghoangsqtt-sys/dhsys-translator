# Phase 7 — Provider Việt Nam/quốc tế và free-first guidance

Status: in_progress. Request: ENH-007. Target line: 4.15.0 provisional; product manifest remains 4.14 until the independent release gates pass.

## Goal

Make the default desktop provider surfaces useful for Vietnamese/global users with a zero-API-cost preference, while retaining every legacy provider ID and an explicit advanced path to all integrations.

## Compatibility contract

- Provider registries remain contiguous and unchanged: translation `0..28`, recognition `0..32`, TTS `0..37`.
- Hiding is presentation-only. Processing, CLI, WebUI, persisted numeric indexes, credentials, Chinese media languages and dynamic import modules remain available.
- A saved hidden provider is never silently replaced; it stays visible as the active selection.
- The show-all preference is reversible and persisted without deleting any saved setting.

## Cost/readiness vocabulary

| Class | Meaning |
| --- | --- |
| Local model | No provider API charge; may require model download, disk/RAM/GPU and license review |
| Online, no key | No API key in the current adapter; requires Internet and may be rate-limited, changed or unavailable |
| API account | Requires an account/key; trial/free quota may exist but usage can be charged |
| Local endpoint | No provider API charge when self-hosted; the user must install/start the companion server/model |

“Built-in / Tích hợp sẵn” must not be used as a cost promise.

## Task order

1. [7.1](tasks/7.1.md) — central visibility/cost policy and compatibility tests.
2. [7.2](tasks/7.2.md) — filtered menus/comboboxes, show-all control and free-first profile.
3. [7.3](tasks/7.3.md) — Việt/Anh guidance, documentation and regression acceptance.

