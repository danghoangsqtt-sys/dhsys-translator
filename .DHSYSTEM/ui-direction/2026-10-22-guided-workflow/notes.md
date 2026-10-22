# UI Direction — Luồng dịch video có hướng dẫn

## Mục đích

Định hướng cho bốn thay đổi đã chốt trong `docs/brainstorm/session-2026-10-22-guided-workflow.md`: ẩn provider không dùng được ở Việt Nam, màn hình kết quả có trình phát trong app, wizard 3 bước, phụ đề động kiểu karaoke. Prototype chỉ mô tả bố cục; bản thật dùng PySide6/Qt Widgets và tái sử dụng logic, action và params hiện có.

## Pages inventory

| Trang | Vai trò | Trạng thái |
| --- | --- | --- |
| `index.html` | Hub liên kết tới mọi trang | Sẵn sàng duyệt |
| `pages/step1-video.html` | Bước 1: kéo thả video, chọn mục đích (lồng tiếng + phụ đề / chỉ phụ đề / chỉ SRT) | Sẵn sàng duyệt |
| `pages/step2-options.html` | Bước 2: ngôn ngữ, giọng đọc có nghe thử, kiểu phụ đề; "Nâng cao" gập lại; tóm tắt chi phí | Sẵn sàng duyệt |
| `pages/step3-result.html` | Bước 3: tiến độ theo giai đoạn, trình phát kết quả, chuyển Bản dịch/Gốc/Cạnh nhau, file đầu ra | Sẵn sàng duyệt |
| `pages/captions.html` | Xem trước 3 kiểu phụ đề động và tùy chỉnh chung | Sẵn sàng duyệt |
| `pages/providers.html` | Cài đặt nhà cung cấp theo nhóm Miễn phí / API key / Chạy máy; dịch vụ ẩn trong Nâng cao | Sẵn sàng duyệt |

## design_tokens

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
caption_accent: '#FFD84A'
font: 'Segoe UI, system sans-serif'
caption_font: 'Be Vietnam Pro (bundled, OFL)'
radius: '10px'
```

Bảng màu kế thừa `2026-10-04-light-workspace` để không phải đổi `light.qss` toàn bộ.

## Mapping to the current desktop

| Prototype | Qt widget/action hoặc module cần giữ |
| --- | --- |
| Bước 1 chọn file | file chooser hiện có; hàng đợi nhiều video (`task/mult_video.py`) |
| Mục đích | preset ghi vào `subtitle_type`, `tts_type`, `voice_role` hiện có |
| Ngôn ngữ | `source_language`, `target_language` |
| Giọng đọc + Nghe thử | `tts_type`, `voice_role`; `util/ListenVoice.py` |
| Kiểu phụ đề | `subtitle_type` (giữ enum cũ) + trường mới `caption_style` |
| Nâng cao | toàn bộ control cũ, chuyển vào khối gập |
| Bắt đầu dịch | `startbtn` → `win_action.check_start` |
| Tiến độ | tín hiệu `SignMsg` / workflow view state bridge (task 4.2) |
| Trình phát kết quả | `QMediaPlayer` + `QVideoWidget` (đã dùng ở `component/onlyone_set_editdubb.py`) đọc `output_receipt.video_path` |
| Sửa phụ đề & xuất lại | dialog sửa phụ đề hiện có (task 4.13) + chạy lại giai đoạn assemble |
| Nhà cung cấp | `ui/provider_visibility.py` (`CURATED_PROVIDER_IDS`, show-all) |

## Implementation constraints

- Không đổi provider ID, tên action, tín hiệu hay khóa `params/settings`; ẩn chỉ là lớp trình bày.
- Phụ đề động sinh ASS và burn bằng FFmpeg/libass đi kèm; không thêm Node/Chromium.
- Font phụ đề phải có đủ dấu tiếng Việt và được đóng gói (`sp.spec`) để libass không thay font.
- Trình phát cần codec H.264/AAC có sẵn trong backend Qt Multimedia của bản Windows; kiểm tra trong bản frozen.
- "Tất cả công cụ" và menu cũ vẫn truy cập được; wizard không thay thế các công cụ riêng.

## Coverage

| Phase 1–4 feature | UI Direction page |
| --- | --- |
| Ẩn provider không dùng được ở VN | `providers.html`, `step2-options.html` (Nâng cao) |
| Màn hình kết quả + trình phát | `step3-result.html` |
| Wizard 3 bước | `step1-video.html`, `step2-options.html`, `step3-result.html` |
| Phụ đề động (karaoke, nền bo góc, song ngữ) | `captions.html`, `step2-options.html` |

## skills_used

(none)
