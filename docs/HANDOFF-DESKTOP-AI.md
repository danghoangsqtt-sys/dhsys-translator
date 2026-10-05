# Bàn giao dự án cho AI coding trên máy desktop

Repository: `https://github.com/danghoangsqtt-sys/dhsys-translator`

Nhánh tiếp tục mặc định: `main`

## Cách lấy dự án trên máy desktop

```powershell
git clone https://github.com/danghoangsqtt-sys/dhsys-translator.git
cd dhsys-translator
git checkout main
git status
```

Nếu dùng Python 3.12 trên Windows, hãy tạo môi trường riêng và cài dependency theo tài liệu hiện có của repository. Không chép `.venv`, dữ liệu người dùng, API key hoặc thư mục build cũ từ máy này sang.

## Prompt gửi cho AI coding

Sao chép nguyên khối dưới đây vào phiên AI coding mới:

```text
Bạn đang tiếp tục phát triển dự án pyVideoTrans-DH từ repository:
https://github.com/danghoangsqtt-sys/dhsys-translator

Mục tiêu sản phẩm là quy trình dịch/lồng tiếng video ưu tiên người dùng Việt Nam, miễn phí trước, giao diện dễ hiểu, đầu ra phụ đề rõ ràng và TTS tiếng Việt có khả năng xử lý từ tiếng Anh tốt. Không được tự ý xóa provider/model, đổi ID hoặc index đã lưu, xóa hỗ trợ ngôn ngữ nội dung tiếng Trung, hay sửa nội dung SRT chỉ để điều khiển phát âm TTS.

Trước khi sửa code:
1. Chạy `git status`, `git branch -vv`, `git log -5 --oneline` và giữ nguyên mọi thay đổi người dùng chưa commit.
2. Đọc đầy đủ theo thứ tự:
   - `.DHSYSTEM/AI-GUIDE.md`
   - `docs/PLAN.md`
   - `docs/SPEC.md`
   - `docs/brainstorm/session-2026-10-05-vietnamese-first-video-workflow.md`
   - `.DHSYSTEM/ROADMAP.md`
   - `.DHSYSTEM/TRACKER.md`
   - `.DHSYSTEM/phases/4/SPEC.md`
   - `.DHSYSTEM/phases/4/PHASE-STATE.md`
   - `.DHSYSTEM/phases/4/tasks/4.14.md`
3. Kiểm tra commit/tag mới nhất trên `main`. Task 4.13 đã sửa màn hình hiệu chỉnh phụ đề: bảng có tương phản tốt, ô phụ đề có thể double-click để sửa, thời gian có thể chỉnh, và không còn tự đóng do đếm ngược. Bằng chứng local: 9 focused tests, 20 related UI tests và 585 full Python 3.12 tests đều pass (chỉ có một cảnh báo ngoài dự án từ pydub).

Hãy dùng quy trình tự động có checkpoint của `$dh-auto` nếu skill này có sẵn. Bắt đầu từ Task 4.14 — “Make subtitle output explicit and verifiable”; không nhảy thẳng sang TTS hoặc xóa provider.

Yêu cầu Task 4.14:
- Đổi nhãn lựa chọn `subtitle_type` tiếng Việt/Anh để mô tả kết quả người dùng nhìn thấy, không dùng thuật ngữ kỹ thuật mơ hồ.
- Với cài đặt mới trong luồng chính “Tạo video dịch”, mặc định là phụ đề cứng; giữ nguyên mapping enum/giá trị đã lưu của người dùng cũ.
- Phụ đề mềm và không phụ đề vẫn là lựa chọn chủ động.
- Không cho phép chuyển mode âm thầm chọn “không phụ đề”. Cảnh báo rõ trước khi tạo video không có phụ đề.
- Sau khi tạo xong, hiển thị biên nhận đầu ra: chế độ phụ đề, đường dẫn file, và nếu là phụ đề mềm thì player cần bật subtitle track.
- Giữ đúng thứ tự nguồn/đích của các chế độ song ngữ.

Acceptance bắt buộc:
1. Fresh main-workflow task mặc định phụ đề cứng mà không đổi legacy persisted enum mapping.
2. Fixture phụ đề cứng phải nhìn thấy chữ trong decoded frames.
3. Fixture phụ đề mềm có đúng subtitle stream và metadata ngôn ngữ, xác minh bằng `ffprobe`.
4. “Không phụ đề” không bao giờ được chọn âm thầm khi đổi mode.
5. Chế độ song ngữ giữ đúng thứ tự source/target.

Cách thực hiện:
- Trước tiên đánh dấu Task 4.14 `in_progress` trong state/tracker theo quy ước hiện có.
- Tìm toàn bộ nơi đọc/ghi `subtitle_type`, migration/default, các mode transition, pipeline FFmpeg và màn hình kết quả trước khi thay đổi.
- Viết test regression trước hoặc cùng lúc với code. Tách kiểm tra UI/state khỏi kiểm tra media thực.
- Dùng Python 3.12; khi chạy test Qt headless, đặt `QT_QPA_PLATFORM=offscreen` nếu cần.
- Chạy focused tests, related UI tests, rồi full suite. Chạy `git diff --check`.
- Không tuyên bố PASS nếu chưa có bằng chứng media cho hard subtitle và soft subtitle theo contract.
- Cập nhật task contract, phase state, tracker, handoff và tài liệu người dùng tương ứng.
- Commit theo từng checkpoint nhỏ, không dùng `git reset --hard`, không force-push, không ghi đè thay đổi ngoài phạm vi.
- Push lên `main` của remote `https://github.com/danghoangsqtt-sys/dhsys-translator` khi Task 4.14 đạt gate; nếu không đạt, ghi rõ blocker và bằng chứng còn thiếu.

Sau 4.14, thực hiện đúng thứ tự kế hoạch:
- 4.15: đơn giản hóa sidebar và provider profiles nhưng vẫn giữ tương thích legacy.
- 4.16: pilot VieNeu local opt-in và lớp kiểm soát phát âm Việt–Anh; benchmark trước khi chọn mặc định, không sửa displayed SRT.
- 4.17: chỉ giảm provider có kiểm soát sau migration/privacy/local-only evidence; ưu tiên Gemini/OpenRouter miễn phí nhưng phải có fallback và thông báo quota.
- 4.18: end-to-end, frozen Windows, tài liệu và bàn giao.

Kết thúc mỗi task, báo ngắn gọn: thay đổi gì, file chính, test/gate nào pass, phần nào còn mở, commit/tag và trạng thái push.
```

## Trạng thái tại thời điểm bàn giao

- Task đang tiếp tục: **4.14 — đầu ra phụ đề rõ ràng và kiểm chứng được**.
- Task 4.13 đã hoàn tất về code và kiểm thử local; trạng thái persistence được chốt sau khi commit bàn giao này xuất hiện trên GitHub.
- Phase 3 clean-runner/full-media/release gates vẫn độc lập và chưa được phép đánh dấu hoàn tất chỉ vì Phase 4 tiếp tục.
- Không có API key hoặc tệp cấu hình bí mật được chủ động đưa vào commit bàn giao.
