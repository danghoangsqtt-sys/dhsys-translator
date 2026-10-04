# pyVideoTrans WebUI 使用指南

## ⚠️ 重要提示

> **WebUI 版本仅实现了部分功能**，主要用于以下场景：
> - 云服务器部署（远程访问翻译服务）
> - 局域网内部署（服务器与使用机分离）
> - Docker 容器化部署
>
> **如需完整功能**，请使用桌面客户端（`sp.exe`）或源码运行（`sp.py`）。
> 桌面版支持更多 API 渠道配置、实时交互编辑、批量处理等高级功能。

---

## 一、部署方式

### 1.1 源码部署（推荐）

```bash
git clone https://github.com/jianchang512/pyvideotrans.git
cd pyvideotrans
uv sync --extra webui
```

启动服务：

```bash
uv run webui.py                    # 默认仅本机 127.0.0.1:7860
uv run webui.py --port 8080        # 指定端口
uv run webui.py --host 127.0.0.1   # 仅本机访问
uv run webui.py --share            # 公网链接需要先设置 PYVIDEOTRANS_WEBUI_USER/PASSWORD
```

默认访问：`http://127.0.0.1:7860`。使用 `--host 0.0.0.0` 时必须先设置 `PYVIDEOTRANS_WEBUI_USER` 和 `PYVIDEOTRANS_WEBUI_PASSWORD`，并通过反向代理提供 HTTPS 后再供远程访问。

### 1.2 Docker 部署

```bash
# 构建镜像
git clone https://github.com/jianchang512/pyvideotrans.git
cd pyvideotrans
docker build -t pyvideotrans-webui .

# 在构建目录外创建运行时凭据文件；替换下面的示例密码。
printf 'PYVIDEOTRANS_WEBUI_USER=admin\nPYVIDEOTRANS_WEBUI_PASSWORD=change-this-long-password\n' > webui.env

# 运行：容器内监听 0.0.0.0，宿主机只开放本机端口。
docker run -d -p 127.0.0.1:7860:7860 --env-file ./webui.env \
  --name pyvideotrans pyvideotrans-webui

# 持久化配置和输出
mkdir -p data/output data/config
printf '{}\n' > data/config/params.json
printf '{}\n' > data/config/cfg.json
docker run -d -p 127.0.0.1:7860:7860 --env-file ./webui.env \
  --mount type=bind,src="$(pwd)/data/output",dst=/app/output \
  --mount type=bind,src="$(pwd)/data/config/params.json",dst=/app/videotrans/params.json \
  --mount type=bind,src="$(pwd)/data/config/cfg.json",dst=/app/videotrans/cfg.json \
  --name pyvideotrans pyvideotrans-webui

# GPU 加速
docker run -d -p 127.0.0.1:7860:7860 --gpus all --env-file ./webui.env \
  --mount type=bind,src="$(pwd)/data/output",dst=/app/output \
  --mount type=bind,src="$(pwd)/data/config/params.json",dst=/app/videotrans/params.json \
  --mount type=bind,src="$(pwd)/data/config/cfg.json",dst=/app/videotrans/cfg.json \
  --name pyvideotrans pyvideotrans-webui
```

三个 `docker run` 命令是不同的启动方案，只运行其中一个；重复运行前先停止并移除同名容器。浏览器打开 `http://127.0.0.1:7860` 后输入 `webui.env` 中的用户名和密码。`webui.env` 与个人配置不会进入镜像（由 `.dockerignore` 排除）。不要把整个 `/app/videotrans` 目录挂载为卷，否则会覆盖应用源码。

### 1.3 Google Colab

1. 打开 https://colab.research.google.com/drive/1kPTeAMz3LnWRnGmabcz4AWW42hiehmfm?usp=sharing
2. 登录 Google 账号 → 点击 **全部运行**
3. 等待 `*.gradio.live` 链接出现，点击使用

> ⚠️ Colab 免费版有 4-6 小时使用时长限制。

---

## 二、界面说明

WebUI 分为三个标签页：

### 2.1 🎬 视频翻译（主界面）

**文件选择**：支持 mp4/mkv/avi/mov/webm/wav/mp3/m4a/flac 等格式

**语音识别**：可选 faster-whisper/openai-whisper/Qwen-ASR/FunASR/Huggingface_ASR（均为本地内置免费渠道）

**字幕翻译**：可选 Google/Microsoft/M2M100（免费渠道）

**字幕配音**：可选 Edge-TTS/Qwen3-TTS/MOSS-TTS/Piper/VITS/Supertonic/ChatterBox/gTTS（免费/本地内置渠道）

**对齐与字幕**：配音加速、视频慢速、语速/音量/音调调节、字幕嵌入类型

**更多设置**：降噪、标点处理、人声分离、背景声嵌入、CUDA 加速

**硬字幕样式编辑**：字体、颜色、描边、阴影、对齐等全面自定义

### 2.2 ⚙️ 渠道设置

配置各渠道的 API 地址、SK 密钥、模型等。**与桌面版通用**，配置保存在 `videotrans/params.json` 中。

包含：翻译渠道、语音识别渠道、配音渠道、参考音频设置

> 使用 API 渠道前，需先用桌面版（sp.exe）配置好 API 地址和 SK 密钥。

### 2.3 🔧 高级选项

配置全局高级参数，与桌面版 `菜单 → 工具 → 高级选项` 完全通用。

包含：通用设置、视频输出控制、语音识别参数、字幕翻译调整、字幕配音调整、字幕声音画面对齐、Whisper模型提示词

---

## 三、执行翻译

1. 选择视频/音频文件
2. 配置识别/翻译/配音参数
3. 点击「🚀 开始执行」

执行过程：
- 按钮变为「⏳ 执行中...」并禁用
- 右侧日志实时显示 8 个阶段进度
- 完成后按钮恢复，视频预览区可在线播放，文件区可下载

---

## 四、与桌面版对比

| 功能 | WebUI | 桌面版 |
|------|:-----:|:-----:|
| 视频翻译完整流程 | ✅ | ✅ |
| API 渠道（需先用桌面版配置） | ✅ | ✅ |
| 高级选项配置 | ✅ | ✅ |
| 实时交互编辑字幕 | ❌ | ✅ |
| 批量处理 | ❌ | ✅ |
| 视频预览播放 | ✅ | ❌ |
| 远程访问 / Docker | ✅ | ❌ |

---

## 五、常见问题

**Q: 启动报错 No module named gradio**
`uv sync --extra webui`

**Q: Docker 如何持久化配置**
`-v ./data/output:/app/output -v ./data/config:/app/videotrans`

**Q: Docker 如何使用 GPU**
安装 nvidia-container-toolkit 后：`docker run --gpus all ...`

**Q: 如何使用 API 渠道**
先用桌面版配置好 API 地址和 SK，WebUI 自动读取 `params.json`

**Q: 如何创建公网链接**
`uv run webui.py --share`，控制台输出临时 `*.gradio.live` 链接
