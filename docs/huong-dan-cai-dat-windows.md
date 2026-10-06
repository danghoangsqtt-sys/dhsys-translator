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

FFmpeg, ffprobe và tài nguyên UI là thành phần đi kèm bản đóng gói. Nếu các mục này bị thiếu, không cài bản global để che lỗi; hãy dùng đúng gói pyVideoTrans-DH tin cậy để repair/cài lại.

## Nhận và cài bản đóng gói local

Người phát triển có thể gửi trực tiếp bộ file trong `release\local`; GitHub không bắt buộc. Tên file có dạng `pyVideoTrans-DH-<version>-win64-portable.zip`, `pyVideoTrans-DH-<version>-win64-setup.exe`, manifest và các file `.sha256` tương ứng.

Với bản portable, giải nén ZIP ra một thư mục mới rồi chạy `sp\sp.exe`. Không chạy `sp.exe` ngay bên trong ZIP. Bản portable đã mang theo Python runtime, Qt và FFmpeg cần cho ứng dụng, vì vậy máy người nhận không cần cài Python hoặc sửa PATH.

Với bản Setup, chạy file `...-setup.exe`. Installer mặc định cài theo người dùng hiện tại vào `%LOCALAPPDATA%\Programs\pyVideoTrans-DH`, không yêu cầu ứng dụng luôn chạy bằng quyền Administrator và không sửa PATH toàn hệ thống. Shortcut Start Menu và Desktop là lựa chọn trong installer. Cùng một AppId được giữ cho các lần nâng cấp; dữ liệu/cài đặt người dùng ở `%LOCALAPPDATA%\pyVideoTrans` nằm ngoài thư mục chương trình và được giữ lại khi nâng cấp hoặc gỡ cài đặt mặc định.

Trước khi chia sẻ, chạy `powershell -ExecutionPolicy Bypass -File scripts\build_local_distribution.ps1`. Lệnh shipping mặc định yêu cầu đúng Inno Setup `6.7.3`, tạo ZIP, Setup.exe, manifest và SHA-256, sau đó tự chạy bước xác minh. `-SkipInstaller` chỉ dành cho kiểm tra phát triển và không được xem là PASS của Task 5.4.

Có thể xác minh lại một bộ đã tạo bằng `powershell -ExecutionPolicy Bypass -File scripts\verify_local_distribution.ps1`. Kiểm tra sẽ thất bại nếu thiếu file, nội dung bị thay đổi, checksum sai, ZIP có nội dung không khớp inventory hoặc compiler Inno Setup shipping không đúng phiên bản. Bước portable smoke giải nén sang đường dẫn mới, cô lập `%LOCALAPPDATA%` và loại Python khỏi PATH trước khi kiểm tra frozen app.

## SmartScreen, chữ ký và giấy phép

Bản build local chưa ký số có thể hiện cảnh báo Microsoft Defender SmartScreen. Chỉ tiếp tục khi người nhận tin cậy nguồn gửi và SHA-256 khớp sidecar. Khi phát hành rộng rãi, nên ký số executable/installer bằng chứng thư code-signing phù hợp thay vì hướng dẫn người dùng tắt SmartScreen.

pyVideoTrans-DH sử dụng GPLv3. Gói frozen giữ file giấy phép dự án và các license/NOTICE của thư viện bên thứ ba đã được PyInstaller thu thập. Khi phân phối binary cho người khác, cần duy trì khả năng cung cấp mã nguồn tương ứng theo nghĩa vụ GPL và không được xóa các thông báo giấy phép đi kèm.
