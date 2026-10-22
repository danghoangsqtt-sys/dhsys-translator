# Brainstorm Session - 2026-10-22

## Session Info
- **Date**: 2026-10-22
- **Participants**: User, Claude
- **Status**: Completed
- **workflow_version**: 2.19.0
- **upgrade_supplement_version**: ""

## Phases

Phase numbers below are local to this session; `/vp-crystallize` maps them onto the next free project phases (8+).

### Phase 1 — Provider dùng được ở Việt Nam
- Thu hẹp danh sách mặc định còn ba nhóm: Miễn phí không cần key (Google/Microsoft dịch, Edge-TTS, gTTS), API quốc tế (OpenAI, Gemini, OpenRouter), Chạy máy (faster-whisper, Whisper.cpp, Ollama/LM Studio, VieNeu, F5, Piper, Kokoro…) và Custom endpoint.
- Ẩn hẳn mọi cloud Trung Quốc, kể cả DeepSeek, khỏi combo, menu và profile; công tắc "Hiện dịch vụ ẩn" chuyển vào Cài đặt nâng cao.
- Rà mọi chỗ còn lọt (combo chưa đăng ký, dialog công cụ riêng, WebUI, CLI help) và build lại `dist/sp`.

### Phase 2 — Màn hình kết quả
- Sau khi xong: trình phát trong app (QMediaPlayer + QVideoWidget) mở video đầu ra từ `output_receipt`.
- Chuyển Bản dịch / Gốc / Cạnh nhau; nút Mở thư mục, Mở bằng trình phát khác, Sửa phụ đề & xuất lại, Dịch video khác.
- Danh sách file đầu ra (video, SRT nguồn/đích, audio lồng tiếng) và lịch sử kết quả gần đây.

### Phase 3 — Wizard 3 bước
- Bước 1 chọn video + mục đích; Bước 2 ngôn ngữ, giọng (có nghe thử), kiểu phụ đề, tóm tắt chi phí; Bước 3 chạy, tiến độ theo giai đoạn và kết quả (Phase 2).
- Mọi tùy chọn kỹ thuật gập vào "Nâng cao"; "Tất cả công cụ" và menu cũ giữ nguyên.
- Rà toàn bộ nhãn tiếng Việt: bỏ thuật ngữ khó hiểu, bỏ chữ Trung còn sót.

### Phase 4 — Phụ đề động kiểu Remotion
- Sinh ASS có hiệu ứng và burn bằng FFmpeg/libass: Karaoke từng từ, Câu nền bo góc (fade), Song ngữ động.
- Thời gian từng từ: dùng word timestamps khi có; nếu không thì chia theo độ dài âm tiết trong đoạn TTS/phụ đề.
- Đóng gói font có đủ dấu tiếng Việt; tùy chỉnh font, cỡ, màu nhấn, vị trí.

### Phase 5 (and beyond)
- Kiểu 1–3 từ nảy giữa màn hình (TikTok/Shorts) và khung dọc 9:16.
- Căn từ chính xác bằng forced alignment cho phụ đề đã dịch.

## Project meta intake (FEAT-009)

- **status**: skipped
- **profile_id**:
- **profile_path**:
- **binding** (.viepilot/META.md): `.DHSYSTEM/PROJECT-META.md` already exists for this project.

## Meta intake waiver
Project metadata is already bound in `.DHSYSTEM/PROJECT-META.md`; no change requested.

## Architecture diagram applicability inputs

- **Project complexity**: complex (existing 68k-line desktop app; this session changes presentation, output review and subtitle rendering)
- **Services/modules**: single desktop app; touched modules `ui/provider_visibility.py`, `mainwin/`, `ui/`, `task/_stage_subtitle.py`, `task/_stage_assemble.py`, `component/set_ass.py`
- **Event-driven**: yes — Qt signals (`SignMsg`, `output_receipt`) drive progress and the result screen
- **Deployment shape**: local-only Windows PyInstaller onedir; caption font must be bundled
- **User flow complexity**: multi-step (3-step wizard)
- **Integration surface**: low change — no new external service; fewer visible providers
- **Initial diagram hints**: data-flow required (caption style → ASS → FFmpeg); system-overview optional; deployment unchanged except font asset

## Topics Discussed

### Topic 1: Giao diện khó dùng
**Context**: Người dùng thấy quá nhiều tùy chọn, không rõ các bước, cài đặt provider rối, nhãn khó hiểu.

**Discussion**:
- Phase 4 trước đây đã làm sidebar, light workspace và năm công việc cơ bản, nhưng màn hình chính vẫn bày nhiều control kỹ thuật.
- Ba hướng: wizard 3 bước, một màn hình gọn, preset một chạm.

**Decisions**:
- [x] Wizard 3 bước: Chọn video → Ngôn ngữ, giọng & phụ đề → Chạy & xem kết quả.
- [x] Bước 1 có "mục đích" để đặt sẵn lựa chọn bước 2 (lồng tiếng + phụ đề / chỉ phụ đề / chỉ SRT).
- [x] Tùy chọn kỹ thuật gập vào "Nâng cao"; không xóa control hay khóa params cũ.
- [x] Bước 2 hiển thị tóm tắt chi phí ("0 đ · không cần API key") và thời gian ước tính.
- [x] Rà nhãn tiếng Việt và chữ Trung còn sót.

**Open Questions**:
- Wizard thay hẳn màn hình chính hay là chế độ mặc định có nút chuyển về giao diện cũ?
- Có giữ dịch hàng loạt nhiều video trong wizard ở bản đầu không?

### Topic 2: Không xem được video kết quả
**Context**: Khi xong, app chỉ hiện đường dẫn file (`format_output_receipt` trong `mainwin/_actions_task.py`); không có trình phát kết quả.

**Decisions**:
- [x] Trình phát trong app, dùng `QMediaPlayer` + `QVideoWidget` (đã có trong `component/onlyone_set_editdubb.py`).
- [x] So sánh Bản dịch / Gốc / Cạnh nhau; các nút Mở thư mục, Mở bằng trình phát khác, Sửa phụ đề & xuất lại.
- [x] Phụ đề mềm hiển thị được khi phát (đọc từ SRT), không chỉ phụ đề cứng.

**Open Questions**:
- Backend Qt Multimedia (FFmpeg) trong bản frozen có phát được mọi codec đầu ra không? Cần smoke test.

### Topic 3: Phụ đề kiểu Remotion
**Context**: Hiện chỉ có kiểu ASS tĩnh (`component/set_ass.py`). Người dùng muốn phụ đề động như video làm bằng Remotion.

**Discussion**:
- Remotion thật cần Node + Chromium (nặng thêm vài trăm MB, render chậm) và không hợp với bản Windows portable.
- ASS + libass (đã có trong FFmpeg) làm được karaoke `\k`/`\kf`, biến đổi `\t`, fade `\fad`, nền hộp BorderStyle 3.

**Decisions**:
- [x] Dùng ASS + FFmpeg, không thêm Remotion/Node.
- [x] Ba kiểu đầu tiên: Karaoke từng từ, Câu nền bo góc, Song ngữ động.
- [x] Lưu kiểu vào trường mới `caption_style`; không đổi enum `subtitle_type` cũ.
- [x] Đóng gói font có đủ dấu tiếng Việt (đề xuất Be Vietnam Pro, OFL).

**Open Questions**:
- Phụ đề đã dịch không có word timestamps thật. Bản đầu chia theo độ dài âm tiết trong khoảng thời gian của từng đoạn TTS; có cần forced alignment không (đã xếp vào Phase 5)?
- Phụ đề mềm (`mov_text`) không giữ được hiệu ứng; kiểu động chỉ áp dụng cho phụ đề in cứng hay xuất thêm file `.ass`?

**Research Notes**:
- Query: ASS karaoke tags and libass support.
- Sources: Aegisub ASS override tags reference; FFmpeg `subtitles`/`ass` filter (libass).
- Findings: `\k`, `\kf`, `\ko`, `\t`, `\fad`, `\bord`, `\shad` and BorderStyle 3 are rendered by libass, which the bundled FFmpeg uses for the `subtitles`/`ass` filters.
- Recommendation: generate ASS from SRT + per-word timing and reuse the existing hard-subtitle assembly path.

### Topic 4: Quá nhiều provider cloud Trung Quốc
**Context**: ENH-007 (Phase 7) đã có danh sách rút gọn nhưng vẫn giữ DeepSeek và cho bật "Hiện tất cả nhà cung cấp" ngay trên giao diện chính. Bản `dist/sp` đang dùng có thể được build trước Phase 7.

**Decisions**:
- [x] Ẩn hẳn khỏi giao diện, không xóa code hay đổi provider ID (giữ tương thích cấu hình và khả năng merge upstream).
- [x] Nhóm dùng được: Miễn phí không cần key, OpenAI/Gemini/OpenRouter, AI chạy máy. DeepSeek bị ẩn.
- [x] Công tắc hiện dịch vụ ẩn chỉ nằm trong Cài đặt nâng cao.
- [x] Rà và vá mọi chỗ còn lọt, sau đó build lại bản Windows.

**Open Questions**:
- Các dịch vụ quốc tế khác (DeepL, Azure, ElevenLabs, Deepgram) hiện vẫn nằm trong danh sách rút gọn. Người dùng không chọn chúng; đề xuất chuyển vào Nâng cao trừ khi người dùng muốn giữ.
- Nếu người dùng đang chọn sẵn một provider bị ẩn, hiển thị thế nào? (ENH-007 đang giữ nó hiện ra khi được chọn.)

**UI Direction Artifacts**:
- Session id: 2026-10-22-guided-workflow
- Layout: multi-page (`pages/*.html` + hub `index.html`)
- Files:
  - `.DHSYSTEM/ui-direction/2026-10-22-guided-workflow/index.html`
  - `.DHSYSTEM/ui-direction/2026-10-22-guided-workflow/style.css`
  - `.DHSYSTEM/ui-direction/2026-10-22-guided-workflow/notes.md`
  - `.DHSYSTEM/ui-direction/2026-10-22-guided-workflow/pages/{step1-video,step2-options,step3-result,captions,providers}.html`
- Preview focus:
  - step1-video, step2-options, step3-result (wizard), captions (3 kiểu động), providers (nhóm theo cách truy cập)

---

## Summary

Bốn vấn đề được chuyển thành bốn phase theo thứ tự giá trị nhanh trước: (1) ẩn mọi provider cloud không dùng được ở Việt Nam, kể cả DeepSeek, nhưng vẫn giữ ID; (2) màn hình kết quả có trình phát trong app; (3) wizard 3 bước với "Nâng cao" gập lại; (4) phụ đề động karaoke, nền bo góc và song ngữ, sinh bằng ASS + FFmpeg thay vì Remotion.

## Crystallize resolutions (2026-10-22)

- DeepL, Azure (GPT/TTS), ElevenLabs and Deepgram move to Advanced together with every China-hosted cloud provider.
- Animated caption styles apply to hard subtitles only; selecting one switches output to hard subtitles and also writes the styled `.ass` beside the SRT files.
- The wizard is the default start screen; a persisted toggle returns to the classic workspace.
- The wizard supports a multi-video queue from the first release, reusing the existing batch path.
- Crystallized as [ENH-009](../../.DHSYSTEM/requests/ENH-009.md), project phases 8–11 (session phases 1–4); session Phase 5 items stay as backlog.

## Action Items
- [ ] Chạy `/vp-crystallize` để sinh phase 8–11 và task contract.
- [ ] Trả lời các open question về DeepL/Azure/ElevenLabs/Deepgram và cách xử lý phụ đề mềm.
- [ ] Kiểm tra `dist/sp` hiện tại có được build sau commit Phase 7 (`b40a2b6c`) không.
