# Brainstorm — Giao diện sáng, dễ dùng cho Xưởng Video

- Ngày: 2026-10-04
- `workflow_version`: 2.19.0
- Trạng thái: phạm vi giao diện đã chốt; chờ chuyển thành kế hoạch triển khai
- Nguồn: yêu cầu người dùng, `videotrans/ui/en.py`, `videotrans/mainwin/main_win.py`

## Mục tiêu

Làm cửa sổ desktop sáng, dễ đọc và hướng người mới qua một tác vụ video từ đầu đến cuối. Giao diện dùng nền trắng, các sắc xám trung tính và màu nhấn `#14452F`. Tác giả hiển thị là `DHSYSTEM.SYS`. Toàn bộ tính năng hiện có phải tiếp tục tồn tại và truy cập được.

Người dùng phải biết bắt đầu từ đâu trong vài giây: thêm video, chọn ngôn ngữ, kiểm tra đầu ra và bắt đầu xử lý. Các công cụ phụ vẫn truy cập được nhưng không che lấp luồng chính.

## Quyết định đã chốt

- Chỉ thay giao diện Qt Widgets desktop: bố cục, màu, nhãn, trạng thái, điều hướng và khả năng tìm thấy chức năng.
- Giữ nguyên mọi tính năng và hành vi: toàn bộ menu/action, adapter dịch/nhận dạng/TTS, hàng đợi, định dạng đầu ra, CLI, WebUI và cấu hình lưu trữ.
- Không được thay thế menu bằng vài công cụ nhanh. Công cụ nhanh chỉ là lối tắt; danh sách công cụ đầy đủ, cài đặt và menu hiện có phải luôn truy cập được.
- Giữ trang chủ; thay phần không gian làm việc hiện tại bằng bố cục sáng theo luồng tác vụ.
- Thương hiệu hiển thị: `Xưởng Video`; credit ở chân sidebar/About: `DHSYSTEM.SYS`.
- Mặc định ngôn ngữ giao diện vẫn là tiếng Việt; English/中文 giữ qua bộ chọn hiện có.

## Hướng giao diện

### Khung cửa sổ

1. Thanh trên mảnh: tên ứng dụng, trạng thái hàng đợi, nút Trợ giúp và Cài đặt.
2. Sidebar cố định: Trang chủ, Dự án mới, Hàng đợi, Công cụ nhanh và nút **Tất cả công cụ**. Nút này mở đúng danh sách/menu chức năng hiện có, được nhóm lại bằng nhãn dễ hiểu.
3. Vùng chính: một tiêu đề ngắn, vùng kéo thả video, rồi ba bước cấu hình theo thứ tự.
4. Cột phải chỉ chứa tóm tắt đầu ra và cài đặt nâng cao có thể mở rộng; không dồn mọi tùy chọn lên màn hình đầu tiên. Mọi tùy chọn cũ vẫn có mặt trong cài đặt nâng cao hoặc menu đúng chức năng.
5. Thanh hành động cố định dưới cùng: Kiểm tra lại và Bắt đầu xử lý.

### Luồng dự án mới

| Bước | Mục đích | Điều khiển Qt hiện có cần tái dùng |
| --- | --- | --- |
| 1. Thêm video | Chọn hoặc kéo thả video/âm thanh | vùng chọn file hiện có |
| 2. Ngôn ngữ | Chọn tiếng nói gốc và ngôn ngữ đầu ra | `source_language`, `target_language` |
| 3. Tạo đầu ra | Chọn phụ đề, lồng tiếng, vị trí xuất | `subtitle_type`, `tts_type`, `output_dir` |
| 4. Xử lý | Chạy đúng tác vụ hiện có | `startbtn` và `win_action.check_start` |

### Công cụ nhanh

Các mục giữ nguyên hành vi và chỉ đổi vị trí/cách gọi:

- Phiên âm thành phụ đề → `fn_recogn`
- Dịch phụ đề SRT → `fn_fanyisrt`
- Gán nhiều giọng → `fn_peiyinrole`
- Ghép video, âm thanh, SRT → `fn_vas`

## Thiết kế trực quan

```yaml
surface: '#FFFFFF'
surface_subtle: '#F4F6F5'
surface_selected: '#E7F0EB'
ink: '#17211C'
muted: '#65716B'
border: '#D9E0DC'
primary: '#14452F'
primary_hover: '#0E3524'
primary_soft: '#DCEDE4'
focus: '#2F7956'
danger: '#B42318'
font: 'Segoe UI, system sans-serif'
radius: '10px'
```

- Dùng `#14452F` cho hành động chính, trạng thái đang chọn và focus; không phủ màu xanh lên toàn màn hình.
- Giữ tỷ lệ tương phản chữ/nền đủ đọc, kể cả nhãn trạng thái và trường bị vô hiệu hóa.
- Chỉ hiển thị tùy chọn nâng cao khi người dùng mở; trạng thái trống phải nói rõ việc cần làm tiếp theo.

## Không nằm trong phạm vi

- Không viết lại pipeline media hoặc thay đổi yêu cầu API/mô hình.
- Không đổi định dạng cấu hình, đường dẫn output hoặc hợp đồng CLI/WebUI.
- Không thêm timeline, tài khoản, đồng bộ đám mây hoặc WebUI mới.

## Bản phác thảo UI

- [Prototype không gian làm việc sáng](../../.DHSYSTEM/ui-direction/2026-10-04-light-workspace/index.html)
- [Ghi chú UI](../../.DHSYSTEM/ui-direction/2026-10-04-light-workspace/notes.md)

## Coverage

| Nhu cầu | Màn hình/bề mặt | Cách kiểm chứng khi triển khai |
| --- | --- | --- |
| Biết bắt đầu ở đâu | Dự án mới | Trạng thái trống có một hành động “Chọn video” nổi bật |
| Nhìn được tiến trình | Hàng đợi và thanh dưới | Các trạng thái chờ/đang chạy/lỗi/xong lấy từ task hiện có |
| Giữ công cụ cũ | Sidebar + công cụ nhanh | Smoke mở `fn_recogn`, `fn_fanyisrt`, `fn_peiyinrole`, `fn_vas` |
| Giữ toàn bộ chức năng | Menu, sidebar, cài đặt nâng cao | Lập bảng ánh xạ từng action cũ sang vị trí mới; smoke tất cả menu động |
| Không đổi nghiệp vụ | Main window và actions | Regression test + smoke gói Windows |

## Phases

| Phase | Khả năng | Điều kiện hoàn tất |
| --- | --- | --- |
| 4.4 | Theme sáng, shell điều hướng, trang Dự án mới | Không thay đổi action/task; có kiểm tra keyboard/focus và 1280×720 |
| 4.5 | Gắn widget hiện có vào ba bước, cài đặt nâng cao và trạng thái hàng đợi | Một video mẫu chạy bằng đúng pipeline cũ; mọi action cũ có vị trí truy cập mới |
| 4.6 | Hồi quy UI, tiếng Việt/Anh/Trung và gói Windows | Test nguồn, smoke toàn bộ sidebar/menu động/gói Windows đạt |

## Còn mở

- Tên sản phẩm `Xưởng Video` tiếp tục là tên hiển thị tạm; `DHSYSTEM.SYS` là credit tác giả đã chốt.
- Bản đầu chỉ ưu tiên desktop; WebUI giữ nguyên giao diện.

## Hành động tiếp theo

Chuyển session này thành nhiệm vụ Phase 4 với kế hoạch tái sử dụng widget/action hiện có, sau đó mới sửa mã giao diện.

## Crystallized implementation

- Approved scope became PLAN tasks 4.4?4.6 and SPEC UI-05?UI-07.
- Implementation preserves the generated workspace and existing QAction instances; it changes only the presentation shell, theme and home/about surfaces.
- Local evidence: 10 focused UI tests, 549 full Python 3.12 tests, and offscreen smoke screenshots at 1280?720 and 1920?1080.
