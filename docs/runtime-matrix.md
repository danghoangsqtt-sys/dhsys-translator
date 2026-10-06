# Runtime matrix — 2026-10-04

The Windows candidate workflow uses Python 3.12.13. The manifest allows Python 3.10–3.12 for source use, but a green unit suite alone does not establish packaged media compatibility.

| Windows runtime | Install evidence | Unit tests | Packaging/media smoke | Decision |
| --- | --- | --- | --- | --- |
| Python 3.10.19 | Locked core + `wetext` installed | 540 passed | Source CLI/GUI smoke; PyInstaller `torchaudio` hook stack overflow | Source runtime verified locally; not candidate build runtime |
| Python 3.11.15 | Isolated locked core + `wetext` installed | 540 passed | CLI help/list and GUI locale import; packaged media pending | Core and extra verified locally |
| Python 3.12.13 | Isolated locked core + `wetext` installed | 540 passed | Local extracted ZIP: CLI/provider/dialog/SRT/MP4 smoke and read-only GUI twice pass; full provider-backed flow pending | Windows candidate build runtime |

`wetext` now selects separate pinned Windows `pynini` wheels for the `cp310`, `cp311`, and `cp312` ABIs. Each runtime installed the extra and imported `pynini` 2.1.6.post1; WeTextProcessing 1.2.0 metadata was present. This does not prove every optional voice channel's media path.

`uv lock --check --offline` resolves 424 packages. Chatterbox and Perth sources are pinned to Git commits (`5de7a54a` and `ce86c49d`); the former mutable `master.tar.gz` source is removed from the manifest and lockfile. Fresh online checkout on a clean runner is still required to confirm network availability.

The candidate build workflow uses Python 3.12.13. A local PyInstaller onedir artifact passed packaged dynamic provider/dialog and CLI version checks, SRT parsing, and FFmpeg MP4 generation with audio and video. Windows `tar.exe` created a 3.69 GB ZIP; SHA-256 `fdfcf1c791074c02d14cba6709652cae09c14529c75f9f128e38f1fbd00da90c` matched before `Expand-Archive`. The extracted GUI launched twice from another CWD under an NTFS content-write deny and wrote user data outside the install. A clean runner and a full provider-backed STT/TTS media flow remain open. No GitHub Release is created by the candidate workflow.

The prior empty-cache offline check could not fetch a GitHub source; offline operation with an empty cache is not a clean-install test. The pinned commit was fetched and built in the Python 3.11 environment, then the full suite passed. The candidate workflow still needs to run on a clean Windows runner.

The Windows workflow now selects FFmpeg `ffmpeg-N-127142-g12b7b9891b-win64-gpl.zip` from the fixed `autobuild-2026-10-03-18-14` release and checks SHA-256 `a885f564dee2b60f69ab866c6c89b96ae531fc2ee1f24ff8b5b1a6d29960a96b` before extraction. A local download matched that hash and contained both `bin/ffmpeg.exe` and `bin/ffprobe.exe`. The clean runner has not executed this workflow yet.
Those binaries also generated a 0.3 second MP4 with audio and video streams in a local smoke check.

## Installed recipient lifecycle

On 2026-10-06 the unsigned Setup artifact `A245DFF2E3D65FB0C623079156F5839C1E6A509DE03F0A0005EF0E10C6BDCF0C` passed a developer-host recipient simulation with Python removed from PATH and isolated program, user-data and process-temp directories. Installation, two core launches, Vietnamese and English frozen UI, hard/soft subtitle media checks, execution from a write-denied program tree, same-version in-place upgrade, uninstall and user-data preservation all passed. The System Check reported the actual Windows 11/AMD64 machine facts; the basic workload was ready, local models degraded only because the CUDA driver level was unknown, and CUDA acceleration remained unknown rather than being guessed ready.

This evidence is intentionally marked `partial`: shortcuts, SmartScreen interaction and the complete lifecycle still require Windows Sandbox, a disposable VM or a clean user profile. The local Setup has no Authenticode signature, so it is not a broadly trusted distribution candidate.

## System readiness ratings

The local Windows distribution exposes machine facts separately from workload ratings. The
diagnostic payload uses stable codes and does not export usernames, full local paths, media
filenames, API keys, provider credentials or arbitrary environment values.

| Capability | Basic translate/dub | Local models | NVIDIA/CUDA acceleration |
| --- | --- | --- | --- |
| Bundled FFmpeg + ffprobe | Required | Required | Required |
| Bundled application resources | Required | Required | Required |
| Writable user-data + cache | Required | Required | Required |
| RAM | 4 GiB minimum, 8 GiB recommended | 4 GiB minimum; more is recommended per model | Recommended |
| Free disk | 4 GiB minimum, 12 GiB recommended | 4 GiB minimum; model downloads need additional space | 4 GiB minimum |
| CPU | CPU-only is supported; 4 logical threads recommended | Recommended | Optional |
| NVIDIA GPU / CUDA driver visibility | Optional | Recommended | Required |

`ready` means every required fact is present and no recommended item is missing. `degraded`
means required items are present but a recommended capability is missing or unknown. `blocked`
means a required capability is known to be missing. `unknown` is kept distinct when a required
probe cannot be completed; diagnostics do not guess that unknown hardware is absent.

GPU probing uses bounded `nvidia-smi` subprocess calls with argument lists and short timeouts.
Failure to find or query `nvidia-smi` does not block the basic CPU workflow. The CUDA value is
the driver-supported CUDA level reported by `nvidia-smi`; it is not a claim that every optional
local model has a compatible CUDA runtime installed.
