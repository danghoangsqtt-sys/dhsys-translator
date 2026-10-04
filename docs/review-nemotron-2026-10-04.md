# Rà soát phần mã được bổ sung ngày 2026-10-04

> **Biên bản lịch sử:** các số liệu và lựa chọn Python 3.10 bên dưới là ảnh chụp tại thời điểm rà soát. Sau đó dự án đã kiểm chứng thêm Python 3.11/3.12, đạt 540 test và chuyển workflow Windows ứng viên sang 3.12.13. Trạng thái hiện hành nằm ở [runtime matrix](runtime-matrix.md) và [task 3.3](../.DHSYSTEM/phases/3/tasks/3.3.md).

## Đã kiểm tra và sửa

| Vấn đề | Bằng chứng | Xử lý |
| --- | --- | --- |
| CLI `--help` lỗi `ValueError: unsupported format character` vì dấu `%` trong help text | Chạy trực tiếp `cli.py --help` trước sửa thất bại | Khôi phục chuỗi help song ngữ và cách escape `%`; thêm kiểm thử `format_help()` |
| CLI mất toàn bộ bản dịch tiếng Trung và `set_lang('zh')` không còn tác dụng | Đối chiếu `cli.py` với `HEAD` | Khôi phục bảng dịch và kiểm thử song ngữ; giữ phiên bản CLI 4.14 |
| Workflow gọi `sp.spec` trong khi `*.spec` bị Git bỏ qua | `.gitignore` và `git status` | Cho phép `sp.spec` được theo dõi |
| Spec tạo một file, workflow tìm `dist/sp/sp.exe` | Đối chiếu `EXE`/`COLLECT` với đường dẫn workflow | Chuyển sang onedir; chép tài nguyên cần thiết cạnh executable |
| Tag có thể phát hành tự động khi chưa chạy smoke trên gói | Workflow ban đầu | Chỉ còn `workflow_dispatch` tạo artifact ứng viên; không tạo GitHub Release |
| Spec có thể gom model/cache cá nhân và lọc dữ liệu hook quá rộng | Nội dung `sp.spec` | Không gom model/cache; bỏ bộ lọc theo chuỗi `test` dễ xóa nhầm tài nguyên |

Workflow ứng viên dùng Python 3.10.19, uv 0.10.9 và xuất ZIP kèm tệp SHA-256. `version.txt` được PyInstaller đọc thành `VSVersionInfo`. Những sửa đổi này mới được kiểm tra tĩnh và bằng unit test; build trên runner sạch chưa được xác nhận.

## Còn mở trước khi phát hành

1. `pyproject.toml` công bố Python 3.10–3.12. Bộ kiểm thử chạy tốt trên 3.10 và 3.12 (**518 passed** mỗi môi trường), nhưng Python 3.11 chưa thử, GUI và media smoke trên 3.12 chưa chạy. Extra `wetext` dùng wheel Pynini `cp310`, nên cài trên 3.12 thất bại. Chỉ dùng 3.10 làm runtime đóng gói hiện tại.
2. Workflow cần chạy trên Windows runner sạch; sau đó giải nén artifact, mở `sp.exe` hai lần và chạy fixture SRT/MP4, kiểm tra FFmpeg, icon/font, thư mục ghi và SHA-256. Không xem unit test là bằng chứng gói sử dụng được.
3. Nguồn FFmpeg `ffmpeg-git-full.7z` và dependency Chatterbox từ `master.tar.gz` là URL thay đổi theo thời gian. Cần ghim phiên bản và checksum trước khi yêu cầu build tái lập. Lệnh `uv lock --check --offline` với cache workspace mới không lấy được Chatterbox; lần kiểm tra lock trước đó với cache sẵn có đã đạt.
4. `webui.py` được dịch hàng loạt từ tiếng Trung sang tiếng Anh, gồm giá trị mặc định `CLI_LANG`. Đây là thay đổi sản phẩm ngoài phạm vi sửa lỗi; cần quyết định ngôn ngữ và kiểm tra thủ công UI trước khi nhận vào bản phát hành. Các bản sửa bảo vệ WebUI từ giai đoạn trước đang nằm chung trong file này.
5. Toàn bộ sửa đổi còn ở working tree. Repository đang trỏ tới upstream, chưa có commit/fork để lưu mốc thay đổi an toàn.

## Kiểm chứng đã chạy

- `cli.py --help` và `--version`: đạt, phiên bản in ra 4.14.
- `pytest -q` Python 3.10.19: 518 passed.
- `pytest -q` Python 3.12.13 trong môi trường core tách riêng: 518 passed.
- `py_compile` cho `cli.py`, `webui.py`, `sp.spec`: đạt.
- Parse workflow YAML, parse `version.txt` bằng PyInstaller, `git diff --check`: đạt.

Trạng thái Phase 3: đang làm; chưa đạt cổng phát hành.
