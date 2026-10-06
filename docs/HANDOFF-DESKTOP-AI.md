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
   - `.DHSYSTEM/phases/3/PHASE-STATE.md`
   - `.DHSYSTEM/phases/4/SPEC.md`
   - `.DHSYSTEM/phases/4/PHASE-STATE.md`
   - `.DHSYSTEM/phases/4/tasks/4.18.md`
3. Kiểm tra commit/tag mới nhất trên `main`. ENH-004 tasks 4.13–4.18 đã PASS. Task 4.18 có bằng chứng source và Windows frozen hiện tại: 72 focused, 349 related UI/config/CLI/WebUI, 658 full Python 3.12.14 tests; frozen core/UI/sidebar/dynamic-menu smoke pass; hard subtitle có decoded-frame delta `40953`; soft subtitle có đúng một stream `mov_text` với `language=vie`.

Hãy dùng quy trình tự động có checkpoint nếu skill tương ứng có sẵn. Không chạy lại hoặc sửa ngược các quyết định đã chốt của 4.13–4.18 nếu không có regression mới.

Các ràng buộc sản phẩm đã chốt:
- `subtitle_type=1` vẫn là phụ đề cứng và là mặc định cho task mới trong luồng chính; legacy persisted enum mapping không đổi.
- Không mode nào được âm thầm chọn “không phụ đề”; soft subtitle vẫn cần bật subtitle track trong player.
- Provider registry giữ translation `0..28`, recognition `0..32`, TTS `0..37`; không xóa/ẩn/đổi số provider/model đã lưu.
- Local profile chỉ là local-only khi endpoint Local LLM là loopback. Gemini/OpenRouter là remote/off-device và phải giữ privacy/quota/fallback messaging.
- VieNeu tiếp tục là local opt-in qua adapter OpenAI-compatible. Người dùng đã chọn **Hải Đăng** làm giọng pilot ưu tiên; không ép thành global default và vẫn giữ các giọng khác để chọn theo nội dung/nam-nữ/nhiều speaker.
- Điều khiển phát âm Việt–Anh dùng `tts_text` transient/project glossary; không sửa displayed/persisted SRT.
- `zh-cn`, `zh-tw`, `yue` vẫn là ngôn ngữ nội dung được hỗ trợ.

Việc tiếp theo của dự án là quay lại **Phase 3 Task 3.3 clean-runner/full-media/release gate**. Phase 4 PASS không được dùng để suy ra Phase 3 đã hoàn tất. Chỉ đánh dấu release gate khi có đúng bằng chứng clean runner, provider-backed media và persistence/release theo contract Phase 3.

Kết thúc mỗi task, báo ngắn gọn: thay đổi gì, file chính, test/gate nào pass, phần nào còn mở, commit/tag và trạng thái push.
```

## Trạng thái tại thời điểm bàn giao

- **ENH-004 / Task 4.18 đã PASS local acceptance.** Python 3.12.14 + Qt offscreen: 72 focused, 349 related UI/config/CLI/WebUI và 658 full tests pass; full suite chỉ có một cảnh báo ngoài dự án từ `pydub/audioop`.
- Current frozen candidate `dist/sp/sp.exe` có SHA-256 `A4C7D607B80C15CF04A023B94BA32A2CF4E31BA8F39B2BDBBA889F79B8B18F25`. Core smoke, UI Việt/Anh, sidebar và dynamic menu đều PASS. Hard subtitle decoded-frame delta là `40953`; soft subtitle có đúng một `mov_text` stream với `language=vie`.
- Evidence gọn nằm ở `.DHSYSTEM/phases/4/evidence/task-4.18-source-regression.json` và các file `.DHSYSTEM/phases/4/evidence/task-4.18-frozen-*.json`. Không commit video/WAV sinh ra hoặc credential.
- Tasks 4.13–4.17 vẫn giữ nguyên quyết định tương thích: hard subtitle mặc định cho task mới, provider/profile legacy ID không đổi, VieNeu local opt-in, Hải Đăng là giọng pilot ưu tiên nhưng không phải global default, và SRT hiển thị/lưu trữ không bị sửa để điều khiển phát âm.
- Phase 3 Task 3.3 clean-runner/full provider-backed media/release gates vẫn độc lập và đang mở. Đây là hướng tiếp tục sau ENH-004.
- Không có API key hoặc tệp cấu hình bí mật được chủ động đưa vào commit bàn giao.
