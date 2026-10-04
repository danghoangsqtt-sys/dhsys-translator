# UI Direction — Không gian làm việc sáng

## Mục đích

Định hướng cho cửa sổ làm việc desktop của Xưởng Video. Prototype chỉ mô tả bố cục và thứ bậc thông tin; bản thực tế dùng PySide6/Qt Widgets và tái sử dụng toàn bộ logic, menu và chức năng hiện có.

## Pages inventory

| Trang | Vai trò | Trạng thái |
| --- | --- | --- |
| `index.html` | Không gian Dự án mới với sidebar, ba bước và tóm tắt đầu ra | Sẵn sàng duyệt hướng thiết kế |

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
font: 'Segoe UI, system sans-serif'
radius: '10px'
```

## Mapping to the current desktop

| Prototype | Qt widget/action to preserve |
| --- | --- |
| Chọn video | file chooser hiện có |
| Ngôn ngữ nguồn/đầu ra | `source_language`, `target_language` |
| Đầu ra | `subtitle_type`, `tts_type`, `output_dir` |
| Bắt đầu xử lý | `startbtn` → `win_action.check_start` |
| Công cụ nhanh | các action `fn_recogn`, `fn_fanyisrt`, `fn_peiyinrole`, `fn_vas` |
| Tất cả công cụ / menu | toàn bộ `QAction` và menu động hiện có |

## Implementation constraints

- Không đổi tên action, tín hiệu hoặc dữ liệu `params/settings`.
- Không đặt logic media vào widget mới.
- Cài đặt nâng cao phải giữ khả năng truy cập qua giao diện hiện có, nhưng thu gọn mặc định.
- Lối tắt không được thay thế menu hoặc công cụ cũ; mỗi chức năng phải có một vị trí truy cập rõ ràng trong sidebar, menu hoặc cài đặt nâng cao.
- Kiểm tra focus, tooltip và contrast trước khi thay toàn bộ stylesheet.

## skills_used

```yaml
- dh-brainstorm: UI direction and scope decisions
```
