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
   - `.DHSYSTEM/phases/4/tasks/4.16.md`
3. Kiểm tra commit/tag mới nhất trên `main`. Tasks 4.13–4.15 đã hoàn tất về code/test. Task 4.15 giữ sidebar cơ bản ở năm tác vụ media, tách provider settings khỏi “Tất cả công cụ”, và thêm ba profile đảo ngược mà không đổi legacy provider ID/index hay xóa credential. Bằng chứng local: 11 focused tests, 35 related UI/config tests và 621 full Python 3.12 tests đều pass (chỉ có một cảnh báo ngoài dự án từ pydub).

Hãy dùng quy trình tự động có checkpoint của `$dh-auto` nếu skill này có sẵn. Bắt đầu từ Task 4.16 — “Pilot local VieNeu and Vietnamese–English pronunciation control”; không xóa provider và không sửa displayed SRT để điều khiển phát âm.

Yêu cầu Task 4.16:
- Pilot VieNeu v3 Turbo riêng trên `127.0.0.1` qua endpoint tương thích OpenAI; không thêm VieNeu/model/dependency vào gói chính ở giai đoạn pilot.
- Dùng adapter OpenAI TTS hiện có và giữ Edge TTS làm fallback; OmniVoice vẫn là lựa chọn nâng cao.
- Tạo lớp `tts_text` nội bộ và glossary theo project để xử lý phát âm Việt–Anh mà không thay đổi nội dung SRT hiển thị.
- Có fixture benchmark cho AI, API, ChatGPT, GitHub, Docker, Python, OpenRouter, Gemini, NVIDIA, URL, e-mail và số phiên bản.
- Chỉ so sánh Edge TTS, VieNeu Turbo và OmniVoice trên phần cứng được hỗ trợ và phải lưu bằng chứng audio/metric trước khi cân nhắc mặc định.
- Khi VieNeu local đang chạy, cho phép người dùng chọn các giọng server expose bằng selector hiện có; giữ nguyên provider ID/index và cài đặt role đã lưu nếu discovery lỗi.
- Dùng cùng danh sách role cho công cụ Nhiều người nói để có thể gán giọng khác nhau theo speaker (làm nền cho lồng tiếng Nam/Nữ) mà không sửa displayed SRT.
- Tạo một mẫu thử cùng câu 10 từ cho mọi preset VieNeu được phát hiện trước khi chốt giọng chính; không suy đoán tuổi giọng nếu metadata không có tuổi.

Acceptance bắt buộc:
1. SRT gốc không thay đổi sau bước chuẩn bị phát âm.
2. Glossary override có thứ tự ưu tiên xác định và test được.
3. Benchmark báo phát âm, tự nhiên, continuity giọng và alignment thời lượng; không tuyên bố chất lượng phổ quát.
4. VieNeu pilot lỗi vẫn để Edge TTS và workflow đầu ra hiện tại hoạt động.
5. Không đưa private key, reference audio hoặc local path nhạy cảm vào log/artifact.

Cách thực hiện:
- Trước tiên đánh dấu Task 4.16 `in_progress` trong state/tracker theo quy ước hiện có.
- Khảo sát adapter OpenAI TTS, nơi tạo text gửi TTS, cache/log và cấu trúc project config trước khi sửa.
- Viết regression cho SRT immutability, glossary precedence, fallback và redaction trước hoặc cùng lúc với code.
- Tách benchmark/audio evidence khỏi unit test; không chọn VieNeu làm mặc định nếu chưa có benchmark thực tế đạt ngưỡng.
- Dùng Python 3.12; chạy focused, related TTS/config, full suite và `git diff --check`.
- Cập nhật task contract, phase state, tracker, handoff và tài liệu người dùng; commit theo checkpoint nhỏ.
- Push lên `main` khi Task 4.16 đạt gate; nếu thiếu hardware/VieNeu runtime để benchmark, ghi blocker và giữ pilot opt-in.

Sau 4.16, thực hiện đúng thứ tự kế hoạch:
- 4.17: chỉ giảm provider có kiểm soát sau migration/privacy/local-only evidence; ưu tiên Gemini/OpenRouter miễn phí nhưng phải có fallback và thông báo quota.
- 4.18: end-to-end, frozen Windows, tài liệu và bàn giao.

Kết thúc mỗi task, báo ngắn gọn: thay đổi gì, file chính, test/gate nào pass, phần nào còn mở, commit/tag và trạng thái push.
```

## Trạng thái tại thời điểm bàn giao

- Task đang tiếp tục: **4.16 — VieNeu localhost opt-in và lớp phát âm Việt–Anh không phá SRT**. `tts_text`/project glossary, benchmark harness và local voice discovery đã được triển khai; 53 focused, 185 related TTS/config/UI và 642 full Python 3.12 tests pass (full suite có một cảnh báo ngoài dự án từ `pydub`). Edge đã tạo 12/12 WAV; VieNeu v3 Turbo ONNX/CPU cũng đã chạy thành công trên loopback qua adapter OpenAI-compatible hiện có và tạo 12/12 WAV. Evidence gọn nằm ở `.DHSYSTEM/phases/4/evidence/4.16-edge-benchmark.json`, `.DHSYSTEM/phases/4/evidence/4.16-vieneu-benchmark.json` và `.DHSYSTEM/phases/4/evidence/4.16-vieneu-voice-audition.json`.
- Selector giọng hiện tại tự lấy danh sách `/voices` khi endpoint OpenAI-compatible là VieNeu local, giữ role đã lưu và fallback an toàn khi server không truy cập được. Công cụ **Nhiều người nói** dùng lại các role này để gán giọng khác nhau theo speaker/line mà không sửa SRT. Bộ thử nghe đã tạo đủ 25/25 preset bằng cùng câu 10 từ; WAV để local trong `tmp/`, không commit.
- Người dùng đã nghe bộ 25 giọng và chọn **Hải Đăng** làm giọng VieNeu chính cho pilot. Đây là lựa chọn ưu tiên của pilot, không ghi đè role đã lưu và không biến VieNeu/OpenAI TTS thành provider mặc định; các giọng khác vẫn phải giữ để chọn theo nội dung và gán nam/nữ cho từng speaker.
- Benchmark 12 fixture đã chạy lại riêng với **Hải Đăng**: 12/12 WAV, SHA-256 đối chiếu 12/12 không mismatch, mean duration ratio `0.502`, `1/12` trong ±20%. Evidence: `.DHSYSTEM/phases/4/evidence/4.16-vieneu-hai-dang-benchmark.json`; evidence Mai Anh cũ được giữ nguyên làm lịch sử.
- Script benchmark đã được sửa để lệnh chạy trực tiếp từ repo root hoạt động mà không cần tự đặt `PYTHONPATH`; có regression test subprocess tương ứng. VieNeu vẫn chỉ là pilot local opt-in, không thêm provider ID/dependency mặc định và không sửa SRT hiển thị/lưu trữ.
- Gate 4.16 vẫn mở: giọng chính đã chốt là **Hải Đăng**, nhưng OmniVoice model chưa cài và ba tiêu chí nghe (phát âm, tự nhiên, continuity) trên 12 fixture Hải Đăng vẫn chưa được chốt. Không bắt đầu 4.17 và chưa đổi provider/voice mặc định khi blocker nghe còn tồn tại.
- Tasks 4.13–4.15 đã hoàn tất và được lưu trên GitHub; Task 4.15 kết thúc ở commit `a9aee380` với tags `pyVideoTrans-DH-p4-t4.15` và `pyVideoTrans-DH-p4-t4.15-done`. Bằng chứng: 11 focused, 35 related UI/config và 621 full Python 3.12 tests pass.
- Phase 3 clean-runner/full-media/release gates vẫn độc lập và chưa được phép đánh dấu hoàn tất chỉ vì Phase 4 tiếp tục.
- Không có API key hoặc tệp cấu hình bí mật được chủ động đưa vào commit bàn giao.
