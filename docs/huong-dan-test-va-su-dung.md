# Hướng dẫn kiểm thử và sử dụng pyVideoTrans

Áp dụng cho mã nguồn trong repo này (bản `4.14`), ưu tiên **Windows + PowerShell**. Các lệnh bên dưới chạy tại thư mục gốc dự án, nơi có `pyproject.toml`, `sp.py` và `cli.py`. Tài liệu mô tả chức năng đã có trong mã; các mục phát hành chưa nghiệm thu nằm ở [PLAN](PLAN.md) và [runtime matrix](runtime-matrix.md).

## 1. Chọn cách chạy

| Nhu cầu | Cách chạy | Lưu ý |
| --- | --- | --- |
| Dùng giao diện đầy đủ | `uv run --python 3.12.13 --locked sp.py` | Có trang chủ và không gian làm việc 5 bước; có công cụ phụ trong menu. |
| Tự động hóa, chạy hàng loạt | `uv run --python 3.12.13 --locked cli.py ...` | Bốn tác vụ `stt`, `sts`, `tts`, `vtv`. |
| Dùng trình duyệt | `uv run --python 3.12.13 --locked --extra webui webui.py` | WebUI chỉ có một phần tính năng desktop. |
| Dùng bản Windows đóng gói | Mở `sp.exe` trong thư mục đã giải nén | Dữ liệu người dùng nằm tại `%LOCALAPPDATA%\pyVideoTrans`. |

Python hỗ trợ cho mã nguồn là **3.10–3.12**; bản đóng gói Windows ứng viên chọn **3.12.13**. Không dùng Python 3.13/3.14 để kết luận bộ test của dự án đạt. Bản tải từ trang Releases của dự án gốc có thể khác mã trong checkout này.

## 2. Chuẩn bị môi trường từ mã nguồn

1. Cài `uv`, Python 3.12.13 và FFmpeg. Kiểm tra trong PowerShell:

   ```powershell
   uv --version
   uv python install 3.12.13
   ffmpeg -version
   ffprobe -version
   ```

   Nếu Windows chưa tìm thấy FFmpeg, thêm thư mục chứa `ffmpeg.exe` và `ffprobe.exe` vào `PATH`, mở lại terminal và kiểm tra hai lệnh cuối. Bản đóng gói ứng viên có hai binary trong `dist\sp\ffmpeg`; chạy từ nguồn vẫn cần FFmpeg có thể được chương trình tìm thấy.

2. Tại thư mục gốc repo, kiểm tra lockfile và cài thêm công cụ test:

   ```powershell
   uv lock --check
   uv sync --python 3.12.13 --locked --group dev
   uv run --python 3.12.13 --locked cli.py --version
   uv run --python 3.12.13 --locked cli.py --help
   ```

   Lần đầu cần mạng, dung lượng trống đáng kể và thời gian tải các gói AI/PyTorch. `--locked` giữ đúng `uv.lock`. Nếu dùng Python 3.10 mặc định của `.python-version`, bỏ `--python 3.12.13` và dùng các lệnh còn lại tương tự.

## 3. Kiểm thử tự động

Chạy toàn bộ test từ gốc repo:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
uv run --python 3.12.13 --locked --group dev pytest -q -p no:cacheprovider --basetemp="$env:TEMP\pytransvideo-pytest"
```

`QT_QPA_PLATFORM=offscreen` cho phép phần kiểm tra Qt chạy không cần hiện cửa sổ. `--basetemp` tránh các thư mục tạm cũ bị Windows khóa. Nếu muốn xem một nhóm lỗi cụ thể trước, chạy ví dụ:

```powershell
uv run --python 3.12.13 --locked --group dev pytest -q tests/test_cli.py tests/test_webui_access.py
uv run --python 3.12.13 --locked --group dev pytest -q tests/test_light_workspace.py tests/test_responsive_surfaces.py
```

Kết quả mong đợi là pytest thoát với mã `0` và dòng `... passed`. Trên môi trường Python 3.12.13 của checkout này, ngày **05/10/2026**, lệnh tương đương chạy trực tiếp qua `.venv312\Scripts\python.exe -m pytest` cho **576 passed, 1 warning** (cảnh báo `audioop` của `pydub`). Số lượng test có thể thay đổi khi mã được sửa. Các test này dùng mock ở một số nơi; chúng **chưa chứng minh** API thật, tải mô hình, GPU hoặc bản đóng gói hoạt động hoàn chỉnh.

## 4. Kiểm tra nhanh công cụ media và CLI

Kiểm tra phiên bản, danh sách provider, ngôn ngữ, mô hình:

```powershell
uv run --python 3.12.13 --locked cli.py --version
uv run --python 3.12.13 --locked cli.py --list providers
uv run --python 3.12.13 --locked cli.py --list languages
uv run --python 3.12.13 --locked cli.py --list models
```

Tạo file MP4 2 giây để xác nhận FFmpeg tạo được cả hình và âm thanh (âm thanh chỉ là tiếng bíp, **không dùng để đánh giá nhận dạng lời nói**):

```powershell
New-Item -ItemType Directory -Force .\tmp\manual-smoke | Out-Null
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "color=c=black:s=320x180:r=25" -f lavfi -i "sine=frequency=440:sample_rate=16000" -t 2 -c:v mpeg4 -c:a aac -shortest .\tmp\manual-smoke\sample.mp4
ffprobe -v error -show_entries stream=codec_type -of default=noprint_wrappers=1 .\tmp\manual-smoke\sample.mp4
```

Kết quả cần có hai dòng `codec_type=video` và `codec_type=audio`. Nếu thiếu, kiểm tra lại FFmpeg và file đầu ra trước khi thử pipeline AI.

## 5. Thử chức năng bằng dữ liệu thật

Chuẩn bị một video/audio **10–30 giây có lời nói rõ**, và một file SRT nhỏ. Dùng bản sao để kiểm thử; một số chế độ GUI có lựa chọn dọn kết quả cũ. Với mô hình cục bộ, lần chạy đầu có thể tải mô hình. Các kênh dịch/TTS qua mạng cần kết nối hoặc khóa API tương ứng.

### 5.1. CLI: chuyển giọng nói thành SRT (`stt`)

```powershell
uv run --python 3.12.13 --locked cli.py --task stt --name "C:\media\speech.mp4" --recogn_type 0 --model_name tiny --detect_language vi --output-dir "C:\media\results" --verbose
```

Thay đường dẫn bằng file thật. `recogn_type 0` là faster-whisper; `tiny` phù hợp thử nhanh trên CPU, độ chính xác thấp hơn mô hình lớn. Không thêm `--cuda` khi chưa có NVIDIA/CUDA hoạt động. Khi thành công, CLI in `[Done]` và `[Output Dir]` là **thư mục riêng cho lần chạy**; mở thư mục đó tìm `.srt`, xem câu chữ và mốc thời gian bằng trình soạn thảo văn bản.

### 5.2. CLI: dịch SRT (`sts`)

Tạo ví dụ SRT UTF-8 nếu chưa có:

```powershell
@'
1
00:00:00,000 --> 00:00:02,000
Xin chào mọi người.
'@ | Set-Content -Encoding utf8 .\tmp\manual-smoke\hello.srt
```

```powershell
uv run --python 3.12.13 --locked cli.py --task sts --name ".\tmp\manual-smoke\hello.srt" --source_language_code vi --target_language_code en --translate_type 0 --output-dir ".\tmp\manual-smoke\results" --verbose
```

`translate_type 0` là kênh mặc định; xem `--list providers` để xác nhận số kênh của bản đang chạy. Tác vụ dịch cần kênh đó truy cập được. Kiểm tra file SRT đầu ra: vẫn có số thứ tự, timestamp hợp lệ và câu dịch.

### 5.3. CLI: tạo giọng đọc từ SRT (`tts`)

```powershell
uv run --python 3.12.13 --locked cli.py --task tts --name ".\tmp\manual-smoke\hello.srt" --tts_type 0 --voice_role "vi-VN-HoaiMyNeural" --target_language_code vi --output-dir ".\tmp\manual-smoke\results" --verbose
```

`--voice_role` là bắt buộc. Mã giọng phải thuộc kênh TTS đang chọn; kiểm tra trong giao diện hoặc danh sách provider trước khi thay giọng. Kênh Edge TTS thường cần mạng. Mở file audio trong thư mục đầu ra để nghe và đối chiếu thời lượng với SRT.

### 5.4. CLI: dịch video trọn quy trình (`vtv`)

Chỉ chạy sau khi STT, dịch và TTS riêng lẻ đã hoạt động với các kênh mong muốn:

```powershell
uv run --python 3.12.13 --locked cli.py --task vtv --name "C:\media\speech.mp4" --source_language_code vi --target_language_code en --recogn_type 0 --model_name tiny --translate_type 0 --tts_type 0 --voice_role "en-US-GuyNeural" --subtitle_type 1 --output-dir "C:\media\results" --verbose
```

Mở MP4 kết quả, nghe tiếng, xem phụ đề, kiểm tra mốc đầu/cuối và so thời lượng với video nguồn. `--subtitle_type 1` là phụ đề cứng; các giá trị khác xem `--help` hoặc [hướng dẫn CLI đầy đủ](cli.md). Mỗi lần CLI chạy tạo thư mục kết quả riêng, kể cả khi trùng tên file nguồn. Khi cần chẩn đoán trung gian, dùng `--no-clear-cache` và dọn thủ công sau khi xong.

### 5.5. Kiểm tra video tiếng Trung sang tiếng Việt

Tiếng Trung vẫn là ngôn ngữ **nội dung** được hỗ trợ dù giao diện chỉ có tiếng Việt và tiếng Anh. Dùng clip ngắn có giọng Quan thoại rõ và chạy:

```powershell
uv run --python 3.12.13 --locked cli.py --task vtv --name "C:\media\chinese.mp4" --source_language_code zh-cn --target_language_code vi --recogn_type 0 --model_name tiny --translate_type 0 --tts_type 0 --voice_role "vi-VN-HoaiMyNeural" --subtitle_type 4 --output-dir "C:\media\results" --no-clear-cache
```

Kết quả cần có MP4 với luồng hình/tiếng, SRT nguồn tiếng Trung và SRT tiếng Việt. `zh-cn`, `zh-tw` và tiếng Quảng Đông vẫn xuất hiện trong danh sách ngôn ngữ nội dung của CLI, desktop và WebUI. Các câu tiếng Trung trong SRT hoặc nội dung do provider trả về là dữ liệu video hợp lệ; nhãn trạng thái, tóm tắt tác vụ và lỗi do ứng dụng tạo phải là tiếng Việt hoặc tiếng Anh.

## 6. Dùng giao diện desktop

Chạy từ mã nguồn bằng PowerShell:

```powershell
uv run --python 3.12.13 --locked sp.py
```

Hoặc giải nén toàn bộ bản Windows ứng viên rồi mở `sp.exe`; không chạy ngay trong file ZIP. Trên **trang chủ Xưởng Video**, ngôn ngữ giao diện chỉ có **Tiếng Việt** và **English**; đổi ngôn ngữ sẽ hỏi khởi động lại. `Mở không gian video` dẫn đến màn hình chính. Bốn công cụ nhanh là **Chép lời**, **Dịch SRT**, **Nhiều người nói** và **Ghép video/âm thanh/SRT**. Menu và danh mục công cụ trong không gian làm việc vẫn có các mục nâng cao.

Cài đặt cũ lưu `zh`, `zh_CN`, `zh-cn` hoặc `zh-tw` cho **giao diện** được tự động chuyển sang `en_US` ở lần khởi động tiếp theo; proxy và các cài đặt khác được giữ lại. File giao diện `zh_CN.json` cũ trong dữ liệu người dùng bị bỏ qua. Việc chuyển đổi này không đổi ngôn ngữ nguồn/đích của tác vụ media.

Để thử một video trong màn hình chính:

1. Ở **Chuẩn bị**, chọn file media; có thể chọn nhiều file hoặc chọn cả thư mục. Dùng file nói ngắn cho lần thử đầu.
2. Ở **Chép lời**, chọn ngôn ngữ nói, kênh nhận dạng và mô hình. Bắt đầu với faster-whisper `tiny` trên CPU. Các kênh API cần cấu hình khóa ở menu cài đặt tương ứng.
3. Ở **Dịch**, chọn ngôn ngữ đích và kênh dịch. Nếu chỉ thử chép lời, dùng công cụ **Chép lời** trên trang chủ sẽ ngắn hơn.
4. Ở **Giọng đọc và phụ đề**, chọn kênh TTS, giọng đọc hoặc `No` nếu không lồng tiếng; chọn kiểu phụ đề mong muốn.
5. Ở **Căn thời gian và đầu ra**, giữ tùy chọn mặc định cho lần đầu, chọn **Lưu vào...** nếu muốn thư mục kết quả cụ thể, rồi nhấn **Bắt đầu**. Đợi trạng thái hoàn tất và mở thư mục đầu ra để xem SRT/audio/MP4.

Nếu không chọn nơi lưu, GUI dùng `_video_out` cạnh thư mục video nguồn; một số chế độ đặt kết quả trong thư mục con theo tên và phần mở rộng file. Trước khi chạy lại, đọc kỹ hộp thoại nếu ứng dụng hỏi **dọn kết quả cũ**: chấp nhận có thể xóa nội dung trong thư mục đầu ra của tác vụ. Với bản đóng gói, cấu hình, cache, log và đầu ra mặc định được ghi vào `%LOCALAPPDATA%\pyVideoTrans`, không phải thư mục chứa `sp.exe`.

## 7. Dùng WebUI

```powershell
uv sync --python 3.12.13 --locked --extra webui
uv run --python 3.12.13 --locked --extra webui webui.py
```

Mở `http://127.0.0.1:7860`. Tab video cho phép chọn file, kênh STT/dịch/TTS, ngôn ngữ, rồi bấm bắt đầu; xem tiến độ và tải kết quả trên giao diện. WebUI còn có các tab cấu hình kênh và tùy chọn nâng cao. WebUI chưa thay thế mọi thao tác sửa thủ công và xử lý hàng loạt của desktop; xem [chi tiết WebUI](webui.md).

Khi cần truy cập từ mạng nội bộ, đặt **cả hai** biến môi trường trước khi cho WebUI nghe trên mọi địa chỉ:

```powershell
$env:PYVIDEOTRANS_WEBUI_USER = 'admin'
$env:PYVIDEOTRANS_WEBUI_PASSWORD = 'thay-bang-mat-khau-dai-rieng'
uv run --python 3.12.13 --locked --extra webui webui.py --host 0.0.0.0 --port 7860
```

Địa chỉ `0.0.0.0` là địa chỉ lắng nghe; trên máy khác truy cập IP thực của máy chạy WebUI. Nếu truy cập qua Internet, đặt HTTPS ở reverse proxy. Không lưu mật khẩu mẫu ở trên vào repo. Với Docker, xem các lệnh và mount dữ liệu trong [webui.md](webui.md); chỉ chọn **một** phương án `docker run` tại một thời điểm.

## 8. Kiểm tra bản Windows đóng gói (nếu có)

Kiểm tra `dist\sp\sp.exe`, `dist\sp\ffmpeg\ffmpeg.exe` và `dist\sp\videotrans\styles\light.qss`. Chạy smoke từ **thư mục khác thư mục cài đặt** để phát hiện lỗi đường dẫn tài nguyên:

```powershell
$exe = (Resolve-Path .\dist\sp\sp.exe).Path
$probe = (Resolve-Path .\scripts\smoke_frozen.py).Path
$cli = (Resolve-Path .\cli.py).Path
$report = Join-Path $env:TEMP 'pyvideotrans-frozen-smoke.json'
$process = Start-Process -FilePath $exe -ArgumentList @($probe, $report, $cli) -WorkingDirectory $env:TEMP -WindowStyle Hidden -Wait -PassThru
$process.ExitCode
Get-Content $report
```

Mã thoát cần là `0` và report cần `"status": "pass"`. `sp.exe` là chương trình GUI nên PowerShell có thể không đợi nếu gọi trực tiếp bằng `&`; dùng `Start-Process -Wait` như trên. Script này kiểm tra tài nguyên, FFmpeg, CLI chạy trong interpreter đóng gói, model Silero VAD, dữ liệu chuyển đổi chữ Trung `zhconv`, hai catalog giao diện và MP4 tổng hợp; **không gọi provider thật**. Có thể dùng `scripts\smoke_frozen_ui.py`, `scripts\smoke_sidebar.py` và `scripts\smoke_dynamic_menus.py` theo cú pháp `sp.exe <script> <report.json>` để kiểm tra giao diện/menu. Với `smoke_frozen_ui.py`, chạy lần lượt locale `vi`, `en_US` và cấu hình cũ `zh_CN`; report phải chỉ có hai lựa chọn `vi_VN`/`en_US`, còn `zh_CN` chuyển sang `en_US`. Bản đóng gói vẫn cần thử với video lời nói và provider thực trên máy Windows sạch trước khi phát hành.

## 9. Khi có lỗi

| Triệu chứng | Kiểm tra trước |
| --- | --- |
| `uv`/`ffmpeg`/`ffprobe` không được nhận diện | Cài công cụ, kiểm tra `PATH`, mở terminal mới. |
| `ModuleNotFoundError: gradio` | Chạy `uv sync --python 3.12.13 --locked --extra webui`. |
| CLI báo thiếu `--name`, ngôn ngữ đích hoặc giọng TTS | Xem `cli.py --help`; `sts` cần ngôn ngữ đích, `tts` cần `--voice_role`, `vtv` cần cả ngôn ngữ nguồn và đích. |
| Lần đầu STT rất lâu | Kiểm tra kết nối tải mô hình, dung lượng ổ đĩa; thử mô hình `tiny` trước. |
| Bản đóng gói báo thiếu `silero_vad_v6.onnx` | Dùng bản được build lại từ `sp.spec`; chạy `scripts\smoke_frozen.py` để xác nhận model VAD đã nằm trong `_internal\faster_whisper\assets`. |
| CUDA không hoạt động | Bỏ `--cuda`/bỏ chọn GPU để xác nhận CPU trước; sau đó kiểm tra driver và thư viện CUDA theo môi trường thực. |
| WebUI từ máy khác không vào được | Kiểm tra `--host`, thông tin đăng nhập, firewall và port 7860. Mặc định chỉ nghe `127.0.0.1`. |
| Kết quả không ở chỗ dự kiến | Đọc `[Output Dir]` của CLI; GUI kiểm tra nhãn thư mục lưu và `_video_out`; bản đóng gói kiểm tra `%LOCALAPPDATA%\pyVideoTrans`. |
| Xử lý lỗi nhưng không rõ nguyên nhân | Xem `logs\YYYYMMDD.log` trong gốc mã nguồn, hoặc `%LOCALAPPDATA%\pyVideoTrans\logs` ở bản đóng gói; bỏ khóa API trước khi chia sẻ log. |

Tham khảo thêm: [thiết lập phát triển](dev-setup.md), [tham số CLI](cli.md), [WebUI](webui.md), [FAQ](faq.md), [kế hoạch và phần việc còn mở](PLAN.md).
