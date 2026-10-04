# UI Direction — màn hình mở đầu tiếng Việt

## Mục đích

Bản phác thảo cho splash desktop. Bản thực hiện dùng PySide6/Qt Widgets và chạy offline. Tên “Xưởng Video” là tên hiển thị tạm, chưa phải quyết định thương hiệu.

## Quy tắc

- Không dùng `logo.png`, tên miền `pyvideotrans.com`, liên kết tới website hoặc hình ảnh dự án gốc trên màn hình mở đầu. Rà soát thêm tiêu đề chính, thanh trạng thái và menu trợ giúp khi triển khai nhận diện mới.
- Tiến trình tải hiện bằng tiếng Việt, dùng trạng thái thực từ callback hiện có; không giả lập phần trăm tải nếu chưa đo được.
- Kích thước mục tiêu 560×350 và kiểm tra trên màn hình 1280×720 với scaling Windows 100–200%.
- Giữ vùng tương phản rõ, chữ chính tối thiểu 16 px tương đương trong Qt, hỗ trợ bàn phím và screen reader ở cửa sổ chính.

## Pages inventory

| Trang | Vai trò | Trạng thái |
| --- | --- | --- |
| `index.html` | Bản phác thảo splash; độc lập với website gốc | Đã chuyển thành Qt splash và trang chủ |

Ảnh chụp kiểm tra bố cục: `preview.png` (900×650, thẻ splash bên trong 560×350).

Ảnh Qt thực tế: `qt-splash-preview.png` và `qt-home-preview.png`.

## design_tokens

```yaml
surface: "#101820"
surface_raised: "#18242d"
text: "#f4f7f4"
muted: "#aebec0"
accent: "#6fe0c4"
accent_warm: "#f8bd83"
radius_large: "26px"
font: "Segoe UI, system sans-serif"
```

## Coverage

| Nhu cầu | Bề mặt | Kiểm chứng |
| --- | --- | --- |
| Splash riêng | `index.html` → `sp.py/StartWindow` | Không còn logo/URL gốc; hiển thị trạng thái tải tiếng Việt |
| Tiếng Việt desktop | `vi_VN.json`, Qt Widgets, cài đặt ngôn ngữ | Màn hình chính, sidebar, ba công cụ và lỗi thông dụng hiển thị tiếng Việt |
| Ba mục lỗi | Sidebar `fn_fanyisrt`, `fn_peiyinrole`, `fn_vas` | Mở từ executable mới; log nếu còn lỗi |

## Còn mở

Tên sản phẩm chính thức và luồng biên tập đầy đủ của Phase 4. WebUI nằm ngoài đợt giao diện desktop này.
