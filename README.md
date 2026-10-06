> Sponsors:
> - **[Recall.ai](https://www.recall.ai/product/meeting-transcription-api?utm_source=github&utm_medium=sponsorship&utm_campaign=jianchang512-pyvideotrans) -  Meeting Transcription API**:  If you’re looking for a transcription API for meetings, consider checking out **[Recall.ai](https://www.recall.ai/product/meeting-transcription-api?utm_source=github&utm_medium=sponsorship&utm_campaign=jianchang512-pyvideotrans)** , an API that works with Zoom, Google Meet, Microsoft Teams, and more
> - **[infistar - 160+ 模型,一个 Key](https://www.infistar.cc/register?aff=9H6H7RR9&ref_source=link)**: 字幕翻译还在纠结用 GPT、Claude、Gemini 还是 DeepSeek? infistar 是 OpenAI 兼容中转,一个 Key 随时切 160+ 模型,挑出翻得最准又最省的那个


---

# pyVideoTrans

Current project version: **4.14**.

<div align="center">

**A Powerful Open Source Video Translation / Audio Transcription / AI Dubbing / Subtitle Translation Tool**

[简体中文](docs/README_CN.md) | [**Documentation**](https://pyvideotrans.com) | [**Online Q&A**](https://bbs.pyvideotrans.com)

[![License](https://img.shields.io/badge/License-GPL_v3-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.10--3.12-green.svg)](https://www.python.org/) [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

</div>

**pyVideoTrans** is dedicated to seamlessly converting videos from one language to another, offering a complete workflow that includes speech recognition, subtitle translation, multi-role dubbing, and audio-video synchronization. It supports both local offline deployment and a wide variety of mainstream online APIs.


<img width="1730" height="957" alt="image" src="https://github.com/user-attachments/assets/25d78661-8b73-4f34-a3e5-205c7daba99b" />

---

##  Core Features

> [Technical Architecture and Principles](docs/architecture.md)

- **Fully Automatic Video Translation**: One-click workflow: Speech Recognition (ASR) → Subtitle Translation → Speech Synthesis (TTS) → Video Synthesis.
- **Audio Transcription / Subtitle Generation**: Batch convert audio/video to SRT subtitles, supporting **Speaker Diarization** to distinguish between different roles.
- **️Multi-Role AI Dubbing**: Assign different AI dubbing voices to different speakers.
- **Voice Cloning**: Integrates models like **F5-TTS, CosyVoice, GPT-SoVITS** for zero-shot voice cloning.
- **Powerful Model Support**:
  - **ASR**: Faster-Whisper (Local), OpenAI Whisper, Alibaba Qwen, ByteDance Volcano, Azure, Google, etc.
  - **LLM Translation**: DeepSeek, ChatGPT, Claude, Gemini, MiniMax, Ollama (Local), Alibaba Bailian, etc.
  - **TTS**: Edge-TTS (Free), OpenAI, Azure, Minimaxi, ChatTTS, ChatterBox, etc.
- **️Interactive Editing**: Supports pausing and manual proofreading at each stage (recognition, translation, dubbing) to ensure accuracy.
- **️Utility Toolkit**: Includes auxiliary tools such as vocal separation, video/subtitle merging, audio-video alignment, and transcript matching.
- **Command Line Interface (CLI)**: Supports headless operation, convenient for server deployment or batch processing.
- **Web Interface (WebUI)**: Browser-based interface for remote access or internal network deployment.


---

##  Quick Start (Windows Users)

pyVideoTrans-DH can be shared directly as a local Windows package; recipients do not need Python, PySide6/Qt or a global FFmpeg installation.

1. **Portable ZIP**: extract `pyVideoTrans-DH-<version>-win64-portable.zip`, open the `sp` folder, then double-click `sp.exe`.
2. **Setup.exe**: run `pyVideoTrans-DH-<version>-win64-setup.exe`. It installs for the current Windows user and can create optional Start Menu/Desktop shortcuts.
3. **Verify before sharing**: keep the matching manifest and `.sha256` files beside the package. Maintainers can run `scripts\verify_local_distribution.ps1` to re-check hashes and the portable contents locally.
4. **Clean-recipient gate**: maintainers should run `scripts\smoke_installed_distribution.ps1 -EnvironmentKind WindowsSandbox` inside Windows Sandbox (or select `DisposableVM`/`CleanUser` truthfully). A developer-host run is diagnostic only and returns `partial`.

> **Note**:
> * Do not run directly from within the compressed archive.
> * The application data under `%LOCALAPPDATA%\pyVideoTrans` is separate from the installed program and is preserved by uninstall by default.
> * Unsigned local builds may trigger Windows SmartScreen. Verify the SHA-256 sidecar before choosing to run a package from a trusted sender.
> * GPU acceleration remains optional; use **Kiểm tra máy / System check** for workload-specific readiness guidance.

---

## ️ Source Deployment (macOS / Linux / Windows Developers)

We recommend using **[`uv`](https://docs.astral.sh/uv/)** for package management for faster speed and better environment isolation.

### 1. Prerequisites

* **Python**: Supported source runtimes are 3.10–3.12. The Windows candidate build uses 3.12.13; see [the runtime matrix](docs/runtime-matrix.md) for verification scope.
* **FFmpeg**: Must be installed and configured in the environment variables.
  * **macOS**: 
  ```
    brew install libsndfile  git  python@3.10
	
	brew uninstall --ignore-dependencies ffmpeg
	
	brew tap homebrew-ffmpeg/ffmpeg
	
	brew install homebrew-ffmpeg/ffmpeg/ffmpeg
  ```
  * **Linux (Ubuntu/Debian)**: `sudo apt-get install ffmpeg libsndfile1-dev`
  * **Windows**: [Download FFmpeg](https://ffmpeg.org/download.html) and configure Path, or place `ffmpeg.exe` and `ffprobe.exe` directly in the project directory.

### 2. Install uv (If not installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Clone and Install

```bash
git clone https://github.com/jianchang512/pyvideotrans.git
cd pyvideotrans
uv sync
```

> WebUI is optional: install it with `uv sync --extra webui`. The `pythonnet` dependency for Whisper.NET on Windows is included in the base installation.
> - To install WebUI: `uv sync --extra webui` 

### 4. Launch Software

**GUI**:
```bash
uv run sp.py
```

**CLI**:
```bash
# Video Translation
uv run cli.py --task vtv --name "./video.mp4" --source_language_code zh-cn --target_language_code en --voice_role "en-US-GuyNeural"

# Audio to Subtitle
uv run cli.py --task stt --name "./audio.wav" --model_name large-v3

# Subtitle Translation
uv run cli.py --task sts --name "./subs.srt" --target_language_code en

# Text to Speech
uv run cli.py --task tts --name "./subs.srt" --voice_role "zh-CN-YunyangNeural"
```

> [CLI documentation with all parameters](docs/cli.md)

**WebUI** (for remote/internal network access):
```bash
uv sync --extra webui
uv run webui.py
```


**Docker** (containerized deployment):
```bash
# Build
docker build -t pyvideotrans-webui .

# Create runtime credentials outside the image build context; change the example password.
printf 'PYVIDEOTRANS_WEBUI_USER=admin\nPYVIDEOTRANS_WEBUI_PASSWORD=change-this-long-password\n' > ../webui.env

# Expose the authenticated UI on the local host.
docker run -d -p 127.0.0.1:7860:7860 --env-file ../webui.env \
  --name pyvideotrans pyvideotrans-webui
```

For persistent output and config mounts, use the file-level mounts in the [WebUI documentation](docs/webui.md).

### 5. (Optional) NVIDIA GPU Acceleration Configuration

If you have an NVIDIA graphics card, execute the following commands to install the CUDA-supported PyTorch version:

```bash
# Uninstall CPU version
uv remove torch torchaudio

# Install CUDA version (Example for CUDA 12.x)
uv add torch==2.7 torchaudio==2.7 --index-url https://download.pytorch.org/whl/cu128
uv add nvidia-cublas-cu12 nvidia-cudnn-cu12
```

> [AMD GPU acceleration via Whisper.NET](docs/whisper_net_setup.md)

---

##  Supported Channels & Models (Partial)

| Category | Channel/Model | Description |
| :--- | :--- | :--- |
| **ASR (Speech Recognition)** | **Faster-Whisper** (Local) | Recommended, fast speed, high accuracy |
| | WhisperX / Parakeet | Supports timestamp alignment & speaker diarization |
| | Alibaba Qwen3-ASR / ByteDance Volcano | Online API, excellent for Chinese |
| **Translation (LLM/MT)** | **DeepSeek** / ChatGPT | Supports context understanding, more natural translation |
| | [infistar AI](https://www.infistar.cc/register?aff=9H6H7RR9&ref_source=link) | infistar - 160+ models, one Key, OpenAI compatible gateway, switch to 160+ models at any time with one Key |
| | MiniMax AI | MiniMax M3 LLM, latest flagship model, OpenAI-compatible |
| | Google / Microsoft | Traditional machine translation, fast speed |
| | Ollama / M2M100 | Fully local offline translation |
| **TTS (Speech Synthesis)** | **Edge-TTS** | Microsoft free interface, natural effect |
| | **F5-TTS / OmniVoice / Qwen3-TTS** | Supports **Voice Cloning** |
| | GPT-SoVITS / Index-TTS / ChatTTS | High-quality open-source TTS, requires local deployment |
| | 302.AI / OpenAI / Azure | High-quality commercial API |

---

##  Documentation & Support

* **Hướng dẫn tiếng Việt**: [Cách cài đặt, kiểm thử và sử dụng](docs/huong-dan-test-va-su-dung.md) | [Mục lục tài liệu](docs/README.md)
* **Official Documentation**: [https://pyvideotrans.com](https://pyvideotrans.com) (Includes detailed tutorials, API configuration guides, FAQ)
* **Online Q&A Community**: [https://bbs.pyvideotrans.com](https://bbs.pyvideotrans.com) (Submit error logs for automated AI analysis and answers)
* **GitHub Wiki**: [architecture.md](docs/architecture.md) | [Add new Translator Channel](docs/dev_extend_en.md) | [cli.md](docs/cli.md) | [webui.md](docs/webui.md) | [Synchronize.md](docs/Synchronize.md) | [faq.md](docs/faq.md)

##  Disclaimer

This software is an open-source, free, non-commercial project. Users are solely responsible for any legal consequences arising from the use of this software (including but not limited to calling third-party APIs or processing copyrighted video content). Please comply with local laws and regulations and the terms of use of relevant service providers.

## Acknowledgements

This project mainly relies on the following open-source projects (partial):

* [FFmpeg](https://github.com/FFmpeg/FFmpeg)
* [PySide6](https://pypi.org/project/PySide6/)
* [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)
* [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
* [openai-whisper](https://github.com/openai/whisper)
* [edge-tts](https://github.com/rany2/edge-tts)
* [F5-TTS](https://github.com/SWivid/F5-TTS)
* [Confucius4-TTS](https://github.com/netease-youdao/Confucius4-TTS)
* [OmniVoice](https://github.com/k2-fsa/omnivoice)
* [CosyVoice](https://github.com/FunAudioLLM/CosyVoice)
* [Gradio](https://www.gradio.app/) (WebUI)

---

*Created by [jianchang512](https://github.com/jianchang512)*


