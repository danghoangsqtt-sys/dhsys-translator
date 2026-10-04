# Brainstorm — Việt hóa và làm mới màn hình mở đầu

- Ngày: 2026-10-04
- `workflow_version`: 2.19.0
- Trạng thái: đang thu thập quyết định; chưa khóa phạm vi triển khai
- Nguồn: phản hồi người dùng, ảnh lỗi, mã `sp.py`, `videotrans/configure/_i18n.py`, `videotrans/ui/en.py`, `videotrans/ui/menu_list.py`, kết quả BUG-016

## Mục tiêu

Người dùng có thể hiểu và vận hành ứng dụng bằng tiếng Việt. Màn hình mở đầu có hình ảnh riêng, hiện đại, không hiển thị thương hiệu, logo hoặc đường dẫn website của dự án gốc. Các lối vào Translate SRT, multiple speaker và Merge V/A/SRT phải mở được trên bản đóng gói được giao.

## Hiện trạng đã kiểm tra

- Giao diện desktop là Qt Widgets/PySide6. `StartWindow` trong `sp.py` là màn hình tải 560×350, dùng `videotrans/styles/logo.png` có chữ `pyvideotrans.com`, đồng thời hiển thị tiến trình tải bằng chuỗi tiếng Anh. Cửa sổ chính là `videotrans/ui/en.py` và vẫn có liên kết đến website gốc trong tiêu đề/thanh trạng thái.
- Bộ bản địa hóa dựa vào `videotrans/language/*.json` và `tr()`. Chỉ có `en_US.json` (1.017 khóa) và `zh_CN.json` (1.019 khóa). `settings.lang` đã tồn tại và `sp.py --lang` được đọc trước khi nhập cấu hình. Thêm tiếng Việt cần bản dịch `vi_VN.json`, lựa chọn ngôn ngữ dễ thấy và rà soát chuỗi viết trực tiếp ngoài `tr()`.
- Các mục sidebar `fn_fanyisrt`, `fn_peiyinrole`, `fn_vas` được nạp qua `get_win`. Ảnh lỗi hiện tại ghi `No module named 'videotrans.winform.fn_recogn'`, đúng với gói Windows cũ. Kiểm tra tiến trình Windows cho thấy PID 18404 đang chạy `E:\data\2.MyProject\2026\pytransvideo-candidate-tar-704404c9eea7421b9c6fbca1eb727fb1\pyVideoTrans-v4.14-windows-x64\sp.exe` (SHA-256 `A78C0846…`), không phải bản mới. Bản `pytransvideo-menus-fixed-de199e560dc343d096ff2a0bc7de3240\sp.exe` (SHA-256 `7A3C3696…`) đã mở 5/5 sidebar và 72/72 menu động từ executable; cả `fn_recogn`, `fn_fanyisrt`, `fn_peiyinrole`, `fn_vas` đều `pass`. Không tạo phiếu lỗi mới cho cùng một artifact cũ.

## Hướng đề xuất

1. **Khôi phục khả năng sử dụng trước:** đóng bản cũ sau khi lưu công việc, chạy executable mới và xác nhận ba mục nêu trên. Nếu chính executable mới còn lỗi, thu log/đường dẫn và sửa trên bản đó.
2. **Việt hóa theo lớp:** thêm `vi_VN` vào cơ chế `tr()`, dịch các luồng chính (màn hình tải, cửa sổ chính, sidebar, ba công cụ đang dùng, trạng thái/lỗi), sau đó rà soát toàn bộ dialog và cài đặt. Giữ tên riêng của dịch vụ và thuật ngữ kỹ thuật cần thiết. Đảm bảo thay đổi ngôn ngữ không làm sai mã ngôn ngữ xử lý media và cho biết khi cần khởi động lại.
3. **Màn hình mở đầu và nhận diện mới:** nền tối dịu, chữ tiếng Việt dễ đọc, biểu tượng trừu tượng gợi khung hình và sóng âm, tên sản phẩm độc lập đang để mở, thanh tiến trình và trạng thái tải. Bỏ logo, tên miền và lời kêu gọi của dự án gốc khỏi splash, tiêu đề chính, thanh trạng thái và các liên kết quảng bá trong menu. Không biến splash thành trang web; triển khai cuối bằng Qt Widgets/Qt painting để chạy offline trong gói Windows. Thông tin giấy phép/phụ thuộc được giữ ở vị trí thích hợp, tách khỏi nhận diện sản phẩm.
4. **Cửa sổ chính:** chỉ thiết kế lại bố cục khi người dùng xác nhận muốn đổi cả cửa sổ sau splash. Nếu chọn, đề xuất trang tổng quan có hành động mới, tác vụ gần đây và lối vào các công cụ chính, gắn với luồng xử lý Qt hiện có.

## Bản phác thảo UI

- [Xem màn hình mở đầu đề xuất](../../.DHSYSTEM/ui-direction/2026-10-04-vi-start/index.html)
- [Ảnh xem trước](../../.DHSYSTEM/ui-direction/2026-10-04-vi-start/preview.png)
- [Ghi chú triển khai](../../.DHSYSTEM/ui-direction/2026-10-04-vi-start/notes.md)
- Bản HTML chỉ để duyệt hướng hình ảnh; sản phẩm desktop sẽ dùng Qt.

## Phases

| Phase | Khả năng | Điều kiện hoàn tất |
| --- | --- | --- |
| 3 — bản vá đang mở | Xác nhận bản chạy đúng và ba cửa sổ hoạt động trong gói Windows | Từ đúng executable bàn giao, 5/5 sidebar và 72/72 menu mở; người dùng xác nhận đường dẫn nếu còn lỗi |
| 4 — giao diện và ngôn ngữ | Tiếng Việt cho desktop và màn hình mở đầu độc lập | Lựa chọn `vi_VN` hoạt động sau khởi động; luồng chính và lỗi thông dụng có tiếng Việt; các bề mặt chính không quảng bá logo/URL gốc; smoke gói Windows đạt |
| 4 — mở rộng có điều kiện | Trang tổng quan mới và/hoặc Việt hóa WebUI | Chỉ chốt sau khi người dùng xác nhận phạm vi; chức năng hiện có vẫn truy cập được |

## Quyết định đang mở

- Đã xác nhận Windows đang chạy executable cũ (PID 18404); người dùng cần chuyển sang bản mới để kiểm tra tương tác thực tế.
- “Trang mở đầu” chỉ là splash hay bao gồm cửa sổ làm việc sau khi tải?
- Chọn trang tổng quan, luồng năm bước hay bố cục tối giản nếu đổi cửa sổ chính?
- Ưu tiên Việt hóa toàn desktop hay cả WebUI? Có muốn dùng tên sản phẩm mới nào không?

## Project meta intake (FEAT-009)

Hoãn vì phạm vi giao diện/ngôn ngữ chưa khóa. Không tạo hồ sơ sản phẩm toàn cục từ tên tạm trong bản phác thảo.

## Hành động tiếp theo

Nhận các lựa chọn đang mở, cập nhật bản phác thảo, rồi chuyển quyết định sang SPEC/PLAN qua `dh-crystallize` trước khi triển khai bằng `dh-auto`. Nếu người dùng muốn triển khai trực tiếp trong phiên này, dùng các quyết định đã chốt làm tiêu chí nghiệm thu.
