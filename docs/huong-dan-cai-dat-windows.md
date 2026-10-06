# Hướng dẫn cài đặt và kiểm tra máy trên Windows

Tài liệu này áp dụng cho bản đóng gói pyVideoTrans-DH chạy local trên Windows. Người nhận phần mềm không cần cài Python, PySide6/Qt hay FFmpeg toàn hệ thống; các thành phần cần thiết của ứng dụng phải được đóng gói cùng bản phát hành.

## Kiểm tra máy trước khi dùng

Mở **Kiểm tra máy** trong ứng dụng. Công cụ quét trạng thái theo ba nhóm: dịch video cơ bản, mô hình chạy local và tăng tốc GPU. Phần quét chỉ đọc thông tin hệ thống và không tự cài đặt hoặc thay đổi cấu hình máy.

Nếu có mục cần xử lý, phần **Khắc phục được đề xuất** chỉ hiển thị các hành động có trong danh sách an toàn cố định của ứng dụng. Trước mọi thao tác mở liên kết hoặc chạy trình cài đặt, ứng dụng phải hiển thị rõ hành động, nhà phát hành, nguồn, đích chính xác, khả năng yêu cầu UAC và khả năng cần khởi động lại. Nút **Không** là lựa chọn mặc định; hủy xác nhận không làm thay đổi hệ thống.

## Quy tắc cài đặt tự động

- Không chạy lệnh shell tự do và không ghép nội dung từ nhãn, đường dẫn hoặc báo cáo hệ thống vào câu lệnh.
- WinGet chỉ được dùng khi máy đã có WinGet và chỉ với package ID cố định trong allowlist. Ứng dụng không tự chấp nhận agreement chưa biết và không bỏ qua kiểm tra hash/bảo mật.
- Nếu WinGet không có hoặc không thể chạy, ứng dụng chỉ mở đường dẫn chính thức đã xác minh hoặc hiển thị hướng dẫn thủ công.
- GPU driver, CUDA và cuDNN không bao giờ được cài âm thầm. Với NVIDIA, ứng dụng chỉ có thể mở trang driver chính thức sau khi người dùng xác nhận.
- Mô hình AI dung lượng lớn không được cài qua generic shell. Việc tải model phải đi qua cơ chế tải model đã có của ứng dụng và vẫn do người dùng chủ động chọn.
- Ứng dụng chính không yêu cầu chạy vĩnh viễn bằng quyền Administrator. Nếu một installer hợp lệ cần nâng quyền, Windows/UAC của installer đó sẽ tự yêu cầu.

## Khi có lỗi

Nếu WinGet không tồn tại, mạng đang offline, người dùng từ chối UAC, installer trả lỗi hoặc Windows yêu cầu khởi động lại, pyVideoTrans-DH phải dừng hành động đó và hiển thị hướng xử lý rõ ràng. Ứng dụng không tự chuyển sang một package khác, không thử lệnh thay thế không nằm trong allowlist và không coi exit code `0` là đủ nếu chưa xác minh post-condition.

Sau khi một prerequisite được cài thành công và post-condition được xác minh, **Kiểm tra máy** sẽ quét lại. Nếu Windows báo cần khởi động lại, hãy khởi động lại trước rồi chạy **Kiểm tra máy** thêm một lần.

## Sửa lỗi gói ứng dụng

FFmpeg, ffprobe và tài nguyên UI là thành phần đi kèm bản đóng gói. Nếu các mục này bị thiếu, không cài bản global để che lỗi; hãy dùng đúng gói pyVideoTrans-DH tin cậy để repair/cài lại. Cơ chế đóng gói portable ZIP và Setup.exe được thực hiện ở Task 5.4.

