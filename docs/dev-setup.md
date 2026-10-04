# Thiết lập phát triển và kiểm thử

Áp dụng cho mã 4.14 trong giai đoạn kiểm thử bản vá. `.python-version` chọn Python 3.10.19 cho build; `pyproject.toml` cho phép Python 3.10–3.12 ở bộ core. Ma trận kiểm thử và giới hạn extra nằm trong [runtime-matrix](runtime-matrix.md). Bản đóng gói vẫn cần kiểm thử trên artifact thật trước khi phát hành.

## Windows: môi trường sạch

1. Cài `uv` và FFmpeg. Kiểm tra `uv --version`, `ffmpeg -version`, `ffprobe -version`.
2. Chọn Python đúng phiên bản: `uv python install 3.12.13` cho candidate Windows, hoặc 3.10–3.12 cho phát triển mã nguồn.
3. Trong thư mục dự án, kiểm tra lockfile: `uv lock --check`.
4. Cài môi trường từ lockfile: `uv sync --locked --group dev`.
5. Chạy bộ test: `uv run --locked --group dev pytest -q -p no:cacheprovider --basetemp="$env:TEMP\pytransvideo-pytest"` trong PowerShell. Dùng thư mục tạm riêng khi workspace có cache pytest cũ bị khóa.

`uv sync` hiện giải quyết hơn 400 gói, trong đó có PyTorch CUDA lớn. Dành đủ chỗ lưu cache và môi trường ảo. Lần đầu cần mạng để tải gói và metadata của nguồn GitHub; `uv lock --check --offline` có thể thất bại dù lockfile hợp lệ nếu cache chưa có nguồn đó.

## Cách đọc kết quả test

- **Unit/regression:** các tệp `tests/test_*.py` dùng mock trong `tests/conftest.py` và dữ liệu nhỏ; mục tiêu là chạy không cần GPU hay API key.
- **Thăm dò phần cứng:** `tests/test_cuda.py` kiểm tra Torch/CUDA, tự bỏ qua nếu không có Torch và không buộc máy có GPU. Kết quả này không thay thế smoke GPU.
- **Kiểm thử tích hợp thực tế:** chạy GUI, FFmpeg, ASR/TTS và ghép video bằng fixture ngắn sau khi có môi trường đầy đủ; được ghi vào cổng G3 của [SPEC](SPEC.md). API trả phí cần môi trường thử riêng, không nằm trong unit gate.

## WebUI

`uv sync --extra webui` rồi chạy `uv run webui.py` để mở trên `127.0.0.1:7860`. Nếu cần truy cập qua mạng hoặc dùng `--share`, đặt cả hai biến môi trường `PYVIDEOTRANS_WEBUI_USER` và `PYVIDEOTRANS_WEBUI_PASSWORD` trước khi chạy `uv run webui.py --host 0.0.0.0`. Không ghi mật khẩu vào đối số dòng lệnh. Triển khai qua Internet cần HTTPS ở reverse proxy hoặc kênh tương đương.

## Kết quả hiện tại (2026-10-04)

- Python 3.10.19, 3.11.15 và 3.12.13 đều đã cài từ lockfile với extra `wetext` và chạy 540 bài test trên từng runtime; workflow candidate dùng 3.12.13 vì PyInstaller 3.10 tràn native stack khi xử lý `torchaudio`.
- `uv lock --check --offline` đạt. Wheel `pynini` Windows được chọn theo ABI `cp310`, `cp311`, `cp312`. Xem bằng chứng chi tiết trong [runtime-matrix](runtime-matrix.md).
- Chưa có smoke trên file Windows đóng gói, vì vậy các bài test trên mã nguồn không phải điều kiện phát hành đã đạt.

## Baseline lịch sử (2026-10-03)

- Máy audit có Python 3.14 và 3.12; đã cài Python 3.10.19 biệt lập để kiểm tra đúng phiên bản.
- `uv lock --check` trên Python 3.10.19: đạt, giải quyết 424 gói.
- Trước khi có môi trường 3.10 đầy đủ, `python -m pytest -q` trên Python 3.14 dừng ở 4 lỗi thu thập test. Nhóm test cấu hình/phụ đề/redaction chạy riêng: 39 đạt, 3 lỗi. Đây là tín hiệu lỗi cần sửa, chưa phải kết quả nghiệm thu trên Python được dự án hỗ trợ.
- `uv sync --locked --group dev` trên Python 3.10.19: đạt; cài 394 gói từ lockfile. Lần đầu cần tải khoảng 3 GiB riêng cho Torch CUDA và có thể bị gián đoạn khi tải nguồn GitHub.
- Chạy toàn bộ pytest: dừng ở 3 lỗi thu thập do các import cũ trong `test_custom_api_url.py`, `test_job_helpers.py`, `test_winform_split.py`.
- Tạm bỏ đúng 3 tệp trên để lấy baseline phần còn lại: **416 đạt, 60 lỗi test**, không còn lỗi setup khi dùng `--basetemp=.pytest_cache/tmp`. Lệnh: `uv run --locked --group dev pytest -q --tb=no --basetemp=.pytest_cache/tmp --ignore=tests/test_custom_api_url.py --ignore=tests/test_job_helpers.py --ignore=tests/test_winform_split.py`. Các lỗi test là đầu vào của task 1.2; không xem baseline này là cổng phát hành đạt.
