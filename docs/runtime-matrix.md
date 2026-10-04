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
