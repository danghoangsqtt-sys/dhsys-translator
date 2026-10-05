# Brainstorm — Luồng tạo video Việt-first: AI, TTS và phụ đề

- Ngày: 2026-10-05
- `workflow_version`: 2.19.0
- Trạng thái: phạm vi đã khóa để lập kế hoạch; chưa thay đổi mã ứng dụng hay xóa nhà cung cấp.
- Nguồn: phản hồi sử dụng thực tế, ảnh màn hình hiệu đính phụ đề và khảo sát mã nguồn hiện tại.

## Mục tiêu sản phẩm

Đưa Xưởng Video về một luồng mặc định dễ dùng tại Việt Nam: người dùng chọn video, nhận dạng, dịch, nghe/hiệu đính, rồi xuất video có phụ đề nhìn thấy được. Sản phẩm vẫn là ứng dụng desktop PySide6 chạy được miễn phí trên máy; dịch vụ API chỉ là tùy chọn có công bố quota, quyền riêng tư và giới hạn.

## Quyết định đã khóa

1. **Không xóa hàng loạt provider/model ngay.** Giao diện cơ bản chỉ hiện các profile được khuyến nghị; provider cũ vẫn còn ở khu vực nâng cao cho tới khi có migration, kiểm thử và quyết định gỡ riêng. Chính sách lựa chọn dựa trên quyền truy cập, chi phí, quyền riêng tư, giấy phép và chất lượng — không dựa vào quốc tịch của model.
2. **Ba profile mặc định:**
   - `Miễn phí trên máy`: faster-whisper, LLM cục bộ tương thích OpenAI và TTS cục bộ.
   - `Gemini API (quota miễn phí)`: Gemini cho dịch/STT khi quota và chính sách dữ liệu phù hợp.
   - `Tùy chỉnh nâng cao`: endpoint tương thích OpenAI, bao gồm OpenRouter hoặc máy cục bộ. OpenRouter/OpenCode không phải backend miễn phí, ổn định mặc định.
3. **TTS Việt–Anh:** thử VieNeu-TTS v3 Turbo qua API OpenAI-compatible chạy `127.0.0.1`; không thêm dependency vào gói chính trong bước thử nghiệm. Edge TTS là fallback. OmniVoice giữ vai trò nâng cao/đa ngôn ngữ, không thay thế VieNeu cho mặc định tiếng Việt.
4. **Phát âm tiếng Anh là một lớp dữ liệu riêng.** Giữ nguyên SRT hiển thị; tạo `tts_text` nội bộ từ bộ dò đoạn Việt/Anh, glossary theo dự án và lựa chọn phát âm. Không phiên âm hàng loạt tiếng Anh sang tiếng Việt. Các đoạn tiếng Anh dài có thể đọc bằng giọng Anh riêng rồi ghép âm thanh nếu người dùng chọn.
5. **Phụ đề hiển thị trực tiếp là mặc định cho “Tạo video dịch”.** Nhãn UI phải phân biệt rõ: phụ đề cứng (hiển thị luôn), phụ đề mềm (bật/tắt trong player), và không xuất phụ đề. Phụ đề mềm là lựa chọn nâng cao, không phải mặc định im lặng.
6. **Hiệu đính phụ đề là thao tác chủ động, không có đếm ngược mặc định.** Không tự đóng/tự lưu; có focus, selection, phím Enter/F2, chỉ báo thay đổi chưa lưu, lưu/tiếp tục rõ ràng.

## Bằng chứng kỹ thuật

- Hai dialog hiệu đính đặt `QTableWidget` ở `NoFocus` và `NoSelection` dù item có cờ editable; đồng thời dùng stylesheet nền tối/chữ `#cccccc` trong cửa sổ sáng. Đây là nguyên nhân trực tiếp cho cảm giác không thể nhấn sửa và tương phản thấp.
- `subtitle_type = 2` hiện là mặc định, nghĩa là phụ đề mềm. Pipeline chỉ burn-in khi loại 1 hoặc 3; vì vậy video có track phụ đề mềm có thể trông như không có phụ đề trong player không tự bật caption.
- `save_and_close()` ghi SRT và `save_and_close2()` tiếp tục không ghi. Nhãn và bố cục hiện tại chưa làm rõ hậu quả đó.

## Luồng trải nghiệm cần đạt

`Chọn video → Chọn profile → Chép lời → Dịch → Hiệu đính (tùy chọn) → Nghe giọng → Xuất`

- Sidebar cơ bản: Tạo video dịch; Chép lời thành SRT; Dịch SRT; Tạo giọng đọc; Ghép/xuất video; Công cụ nâng cao.
- Catalog “Tất cả công cụ” chỉ chứa tác vụ media, không trộn dialog cấu hình provider.
- Màn hình hoàn tất phải nói rõ video có phụ đề cứng, phụ đề mềm hay không có phụ đề; kèm đường dẫn video và SRT.

## Phạm vi và chống tràn phạm vi

Trong đợt này không xây timeline đa lớp, không đổi CLI/WebUI, không xóa nguồn provider, không đưa model/VieNeu vào bản Windows mặc định và không cam kết chất lượng phát âm khi chưa có benchmark. Phụ đề tiếng Trung vẫn là dữ liệu media được hỗ trợ, dù UI chỉ Việt/Anh.

## Phases

| Phase | Nội dung | Điều kiện hoàn tất |
| --- | --- | --- |
| 4.13 | Sửa thao tác, tương phản và trạng thái lưu ở editor phụ đề | Có thể chọn/sửa bằng chuột và bàn phím; không còn tự đóng mặc định; kiểm thử Qt đạt |
| 4.14 | Làm rõ và kiểm chứng đầu ra subtitle | Mặc định video dịch có phụ đề cứng; soft subtitle được mô tả và kiểm chứng bằng `ffprobe`/player |
| 4.15 | UI cơ bản + profile nhà cung cấp | Sidebar/catalog gọn; ba profile hoạt động mà không đổi provider ID hoặc phá cấu hình cũ |
| 4.16 | Pilot VieNeu và lớp phát âm Việt–Anh | VieNeu localhost hoạt động qua adapter hiện có; glossary/benchmark có bằng chứng trước khi bật mặc định |
| 4.17 | Chính sách provider, migration và tối giản có kiểm soát | Audit dependency/config; provider chỉ được ẩn/gỡ sau migration và regression |
| 4.18 | Hồi quy end-to-end, đóng gói và tài liệu | Ba profile, editor và video subtitle cứng/soft qua smoke Windows; hướng dẫn người dùng cập nhật |

## Câu hỏi còn mở khi triển khai

- Máy thử nghiệm VieNeu có CPU/GPU nào, và giọng/loại video đại diện nào sẽ là chuẩn chấm?
- Khi nói “bỏ model Trung Quốc”, có bao gồm cả model chạy cục bộ, hay chỉ các cloud/API không dùng được tại Việt Nam? Kế hoạch hiện không xóa bên nào trước khi có câu trả lời.
- Ngưỡng chất lượng nào cho phép VieNeu trở thành mặc định thay vì chỉ là tùy chọn?

## Nguồn kỹ thuật đã đối chiếu

- VieNeu v3 Turbo là bản mã nguồn mở hiện hành, cung cấp API tương thích OpenAI và chạy CPU ONNX; v3 Nano hy sinh chất lượng Anh/code-switch nên không dùng làm mặc định: https://github.com/pnnbao97/VieNeu-TTS
- sea-g2p là phonemizer cho ngôn ngữ Đông Nam Á và code-switch tiếng Anh, được VieNeu dùng: https://github.com/pnnbao97/sea-g2p
- Gemini Flash-Lite được Google định vị cho dịch khối lượng cao; quota và chính sách dữ liệu phải hiển thị rõ theo tier: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite
- OpenRouter nêu rõ model miễn phí có giới hạn rate và không phù hợp làm dependency sản xuất mặc định: https://openrouter.ai/docs/faq

## Project meta intake (FEAT-009)

Không tạo profile tổ chức mới. Dự án brownfield hiện không có `.DHSYSTEM/META.md`; thông tin tổ chức/tác giả chưa được người dùng xác nhận. Kế hoạch giữ nguyên giấy phép GPL-3.0 và metadata hiện hữu, không suy đoán dữ liệu cá nhân.
