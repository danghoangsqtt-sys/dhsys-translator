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
   - `.DHSYSTEM/phases/4/tasks/4.15.md`
3. Kiểm tra commit/tag mới nhất trên `main`. Tasks 4.13–4.14 đã hoàn tất. Task 4.14 giữ nguyên enum `subtitle_type`, đổi mặc định fresh desktop sang phụ đề cứng, thêm cảnh báo không phụ đề và biên nhận đầu ra. Bằng chứng local: 38 focused tests, 104 related UI tests, 2 real product-pipeline media tests và 613 full Python 3.12 tests đều pass (chỉ có một cảnh báo ngoài dự án từ pydub).

Hãy dùng quy trình tự động có checkpoint của `$dh-auto` nếu skill này có sẵn. Bắt đầu từ Task 4.15 — “Simplify navigation and add provider profiles”; chưa pilot TTS hoặc xóa provider trước khi 4.15 đạt gate.

Yêu cầu Task 4.15:
- Giữ sidebar cơ bản ở năm tác vụ media và một lối vào công cụ nâng cao; mọi QAction cũ vẫn phải truy cập được.
- Không trộn cấu hình provider vào “Tất cả công cụ”; provider được chọn qua profile/cài đặt.
- Thêm ba preset có thể đảo ngược: `Miễn phí trên máy`, `Gemini API (quota miễn phí)` và `Tùy chỉnh nâng cao`.
- Profile chỉ áp cấu hình qua provider ID/index hiện có, không đổi enum/index đã lưu và không xóa provider/model.
- Khi chọn profile remote, hiển thị rõ quyền riêng tư, quota không phải SLA và fallback; luồng cơ bản vẫn dùng được khi chưa có cloud credential.
- Có snapshot/restore để người dùng quay lại cấu hình tùy chỉnh trước đó.

Acceptance bắt buộc:
1. Mọi QAction cũ vẫn truy cập được, nhưng bề mặt cơ bản chỉ hiện tác vụ media.
2. Chuyển profile không làm đổi nghĩa hoặc hỏng provider ID trong cấu hình cũ.
3. Người dùng khôi phục được cấu hình tùy chỉnh sau khi thử profile.
4. Giao diện cơ bản hoạt động khi không cấu hình cloud credential.

Cách thực hiện:
- Trước tiên đánh dấu Task 4.15 `in_progress` trong state/tracker theo quy ước hiện có.
- Khảo sát sidebar/menu/catalog, provider index persistence và các dialog cài đặt trước khi sửa.
- Viết regression cho navigation parity, profile snapshot/restore, legacy ID và zero-cloud-credential path.
- Dùng Python 3.12, `QT_QPA_PLATFORM=offscreen` cho Qt headless; chạy focused, related UI, full suite và `git diff --check`.
- Cập nhật task contract, phase state, tracker, handoff và tài liệu người dùng; commit theo checkpoint nhỏ.
- Push lên `main` khi Task 4.15 đạt gate; nếu không đạt, ghi rõ blocker và bằng chứng thiếu.

Sau 4.15, thực hiện đúng thứ tự kế hoạch:
- 4.16: pilot VieNeu local opt-in và lớp kiểm soát phát âm Việt–Anh; benchmark trước khi chọn mặc định, không sửa displayed SRT.
- 4.17: chỉ giảm provider có kiểm soát sau migration/privacy/local-only evidence; ưu tiên Gemini/OpenRouter miễn phí nhưng phải có fallback và thông báo quota.
- 4.18: end-to-end, frozen Windows, tài liệu và bàn giao.

Kết thúc mỗi task, báo ngắn gọn: thay đổi gì, file chính, test/gate nào pass, phần nào còn mở, commit/tag và trạng thái push.
```

## Trạng thái tại thời điểm bàn giao

- Task tiếp theo: **4.15 — sidebar theo tác vụ và provider profiles có thể đảo ngược**.
- Tasks 4.13–4.14 đã hoàn tất và được lưu trên GitHub; Task 4.14 ở commit `93497188` với hai tag start/done tương ứng.
- Phase 3 clean-runner/full-media/release gates vẫn độc lập và chưa được phép đánh dấu hoàn tất chỉ vì Phase 4 tiếp tục.
- Không có API key hoặc tệp cấu hình bí mật được chủ động đưa vào commit bàn giao.
