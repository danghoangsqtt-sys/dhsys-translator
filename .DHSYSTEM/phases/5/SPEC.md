# Phase 5 — Local Windows distribution and system readiness

Status: in_progress on 2026-10-06. Tasks 5.1–5.2 are PASS locally; Task 5.3 is next. Source request: [ENH-005](../../requests/ENH-005.md). Target product line: **4.15.0 provisional**; the current manifest remains 4.14 until implementation and local distribution acceptance pass.

## Goal

Produce a user-sendable Windows distribution without a GitHub dependency and add a privacy-preserving readiness assistant that explains what the machine can run, what is optional, and what the user may explicitly install or configure.

## Distribution contract

- **Portable ZIP:** contains the frozen application and bundled required runtime assets. The recipient extracts it and launches `sp.exe`; no source Python environment is required.
- **Setup.exe:** installs the same verified frozen tree, creates optional shortcuts, supports upgrade/uninstall, and keeps writable data under the existing `%LOCALAPPDATA%\pyVideoTrans` root rather than the installation directory.
- Both artifacts receive SHA-256 sidecars and are built locally from tracked scripts. Generated artifacts remain untracked.
- The installer is per-user by default so ordinary use does not require Administrator. Any prerequisite that genuinely needs elevation uses normal Windows UAC after explicit confirmation.
- The current onedir baseline is approximately 6.16 GiB before compression. Phase 5 must publish an exact size/composition report and may split optional local-AI/GPU components only when provider IDs remain intact and missing components produce a guided install/readiness result instead of a crash.

## Two-level readiness model

1. **Installer/bootstrap checks:** Windows version/architecture, disk space and runtime prerequisites needed before the PyInstaller app can start.
2. **In-app “Kiểm tra máy”:** CPU/RAM/free disk, GPU name/VRAM when discoverable, NVIDIA/CUDA visibility, bundled FFmpeg/ffprobe, writable user-data/cache paths, network-dependent feature disclosure and optional local companion/model readiness.

The scanner must classify capabilities by workload instead of giving one misleading pass/fail result:

| Workload | Result examples |
| --- | --- |
| Basic video/subtitle workflow | ready, blocked by missing bundled resource, or constrained by disk space |
| CPU STT + cloud/free-first translation/TTS | ready, slow/recommended upgrade, or network/provider action required |
| Local STT/TTS | ready after model download, insufficient RAM/disk, or local endpoint not running |
| GPU acceleration | available, optional but unavailable, or driver/CUDA guidance required |

Thresholds must come from measured candidate size/model requirements and documented provider requirements. Unknown hardware is reported as unknown, never invented as PASS.

## Remediation policy

- Every action shows source/publisher, reason, command or destination, expected privilege and restart impact before execution.
- WinGet may be used only with exact allowlisted IDs and normal agreement/UAC behavior. If unavailable, show an official fallback link or manual instructions.
- The Microsoft Visual C++ runtime may be repaired from Microsoft's official channel only after implementation verifies it is required by the frozen candidate.
- Python, PySide6 and FFmpeg are bundled with the app and are not installed globally on recipient machines.
- GPU drivers, CUDA/cuDNN and large local models are guidance or explicit opt-in flows; driver installation is never automated.
- API keys and provider credentials remain user-entered and are never part of the package.

## Privacy and security

- Do not recursively scan drives, enumerate personal documents, inspect browser data or upload diagnostics automatically.
- Use bounded subprocess timeouts, argument arrays without `shell=True`, exact executable discovery and a fixed remediation allowlist.
- Exported reports redact user names, full private paths, environment secrets, tokens and provider responses.
- Downloads used by the installer/model manager require HTTPS plus expected publisher/hash/signature evidence according to the existing download-integrity rules.

## Task order

1. [5.1](tasks/5.1.md) — pure readiness model and Windows probes.
2. [5.2](tasks/5.2.md) — Vietnamese/English “Kiểm tra máy” UI and sanitized report export.
3. [5.3](tasks/5.3.md) — consent-based, allowlisted remediation actions.
4. [5.4](tasks/5.4.md) — local portable ZIP and Setup.exe build pipeline.
5. [5.5](tasks/5.5.md) — target-machine acceptance, user guide and handoff.

## Acceptance matrix

| Surface | Required evidence |
| --- | --- |
| Scanner | Deterministic tests for CPU/RAM/disk/GPU/runtime/resource outcomes, unsupported/unknown cases and timeouts |
| UI | Việt/Anh frozen UI, clear severity/action wording, refresh/copy/export, no secrets/private-path leakage |
| Remediation | Explicit confirmation, exact allowlist, no shell injection, cancel/failure/reboot/elevation handling |
| Portable | Extract to a different/read-only location; start twice without Python on PATH; create media output and preserve user data |
| Installer | Install/upgrade/uninstall locally; shortcuts work; install tree remains separate from user data; uninstall preserves user data by default |
| Delivery | ZIP/Setup checksums, artifact inventory/size, license notices, recipient instructions and no committed secrets/models/user files |

## Independent gates

This phase does not require GitHub. Phase 3's remote clean-runner gate remains historically open/deferred, but local target-machine acceptance defined here is the authority for direct distribution. A product version bump or public release claim still requires every Phase 5 acceptance item to pass.

## Implementation references

- Microsoft WinGet install contract: `https://learn.microsoft.com/windows/package-manager/winget/install`
- Microsoft supported Visual C++ runtime guidance: `https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist`
- Inno Setup command-line behavior: `https://jrsoftware.org/ishelp/topic_setupcmdline.htm`

These references guide implementation; exact prerequisite necessity, package IDs, hashes and silent/elevation behavior must still be verified against the built candidate before an action is enabled.
