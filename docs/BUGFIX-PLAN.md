# Kế hoạch sửa lỗi sau audit — pyVideoTrans 4.14

Ngày lập: 2026-10-04. Nguồn: `.DHSYSTEM/audit-report.md` và 17 phiếu hiện có trong `.DHSYSTEM/requests/`. Đây là kế hoạch cho bản vá dự kiến **4.14.1**, chưa phải xác nhận phát hành. Nhiều sửa đổi trong hàng đợi đã được kiểm chứng cục bộ; trạng thái hiện hành nằm ở `.DHSYSTEM/TRACKER.md` và Phase 3 state.

## Nguyên tắc và thứ tự

Giữ Phase 3 hiện tại. Các việc 3.1 (ma trận Python) và 3.2 (pipeline Windows) đã có sửa đổi cục bộ nhưng chưa qua cổng artifact; tạm dừng kết luận về chúng. Thực hiện hàng đợi **3.4 → 3.5 → 3.6 → 3.7 → 3.8 → 3.9 → 3.1 → 3.2 → 3.3**. Số hiệu 3.4–3.9 được thêm sau các task đã tồn tại để không đổi định danh và bằng chứng cũ; thứ tự thi công là thứ tự tại đây, không phải thứ tự số học. Trong cùng mức P0, sửa cấu hình/bí mật dễ kiểm chứng trước, rồi bảo toàn dữ liệu, rồi runtime/container.

Mỗi task phải có test tái hiện lỗi trước sửa, thay đổi nhỏ theo đúng vùng mã, test hồi quy liên quan và bằng chứng cổng. Không đánh dấu PASS từ phân tích tĩnh, test mock hoặc kết quả trên Python khác phiên bản đã công bố. Không phát hành hoặc bắt đầu Phase 4 khi P0/P1 chưa được xác nhận trên gói thật. P2 có thể nằm trong bản vá này nếu test đạt; nếu hoãn thì ghi rõ trong release notes.

| Thứ tự | Task | Ưu tiên | Phiếu audit | Kết quả và cổng nghiệm thu |
| --- | --- | --- | --- | --- |
| 1 | 3.4 Cấu hình cũ và bí mật Docker | P0 | BUG-012, BUG-014 | Mở được cấu hình cũ/thiếu trường; build context và image không chứa secret mẫu |
| 2 | 3.5 Bảo toàn cache và đầu ra CLI | P0 | BUG-001, BUG-002 | Dừng/hoàn thành không xóa ngoài cache; hai video trùng tên từ hai thư mục và lần chạy lại không ghi đè âm thầm |
| 3 | 3.6 Docker WebUI và đường dẫn frozen | P0 | BUG-003, BUG-004 | Container truy cập được bằng xác thực; gói mở từ CWD khác và thư mục cài chỉ đọc |
| 4 | 3.7 TLS và vòng đời FFmpeg | P1 | BUG-006, BUG-005 | CA tùy chỉnh còn hiệu lực; đóng GUI chỉ dừng tiến trình con do ứng dụng tạo |
| 5 | 3.8 Tải mô hình tin cậy | P1 | BUG-015, BUG-013 | Tệp hỏng bị tải lại nguyên tử; tải đồng thời không sửa trạng thái toàn cục gây tranh chấp |
| 6 | 3.9 Ngôn ngữ và test hành vi | P1/P2 | BUG-008, BUG-010, ENH-001 | Cấu hình WebUI cũ chọn đúng giá trị; `--lang` hoạt động; test gọi mã sản phẩm và phát hiện hồi quy thực |
| 7 | 3.1 Ma trận runtime và nguồn phụ thuộc | P1 | BUG-009 | Công bố đúng giới hạn 3.10–3.12 và optional extras; nguồn phát hành bất biến hoặc có checksum; lock/install được kiểm tra |
| 8 | 3.2 Gói Windows và cửa sổ động | P0/P1 | BUG-007, BUG-016 | Artifact gọi được provider/dialog, mở cả năm mục sidebar và import đủ 72 menu động |
| 9 | 3.3 Cổng phát hành và đồng bộ tài liệu | P2 | BUG-011 | README, dev setup, task state, HANDOFF khớp manifest đã kiểm chứng; smoke media/gói, checksum và changelog hoàn chỉnh |

## Cổng thực thi

**G3a — an toàn trước đóng gói:** 3.4–3.6 hoàn thành với test tái hiện và hồi quy; đặc biệt xác nhận dữ liệu của người dùng và bí mật không bị ảnh hưởng. Chỉ sau đó tiếp tục hoàn tất 3.1/3.2.

**G3b — độ tin cậy:** 3.7–3.9 hoàn thành, test hành vi thay các test không ràng buộc; kiểm tra CA, FFmpeg và downloader bằng tình huống thật hoặc fixture điều khiển được. Mỗi phiếu audit chỉ đóng khi bằng chứng chạm đúng điều kiện nghiệm thu của phiếu.

**G3c — phát hành 4.14.1:** Chạy cài sạch và bộ test bắt buộc trên từng Python được tuyên bố; build Windows CPU trên runner sạch; giải nén ở thư mục mới và smoke GUI, CLI, SRT/MP4, provider động, khởi động lần hai; kiểm tra container WebUI và image không chứa secret; xác nhận checksum. GPU và optional extras chỉ được ghi là hỗ trợ nếu đã kiểm chứng tương ứng. Tăng phiên bản manifest/CLI và ghi changelog khi cổng này đạt; hiện vẫn là 4.14.

## Phụ thuộc và rủi ro còn mở

- `wetext` hiện chọn wheel Windows riêng cho cp310/cp311/cp312 và đã cài trong môi trường khóa trên cả ba runtime; kiểm chứng từ runner sạch và luồng media vẫn còn mở.
- Chatterbox/Perth đã ghim commit và FFmpeg Windows ứng viên có bản cùng SHA-256 cố định; runner sạch vẫn phải xác nhận đầu vào tải được (BUG-009).
- Spec PyInstaller và module động đã được kiểm tra bằng executable trong ZIP giải nén tại máy cục bộ; cần lặp lại trên runner Windows sạch (BUG-007).
- Các sửa đổi Phase 1–3 đã được lưu ở commit cục bộ `fbcd924f` trên nhánh `codex/phase3-release-gate`; chưa có upstream/push hoặc runner sạch. Giữ bằng chứng “verified locally” tách với “released”.

## Kết quả cục bộ mới nhất — 2026-10-04

Task 3.2 và 3.6 đã qua smoke cục bộ trên artifact Python 3.12.13: provider và dialog nạp động, CLI báo phiên bản, SRT được đọc, FFmpeg tạo MP4 có âm thanh và hình ảnh. ZIP 3,69 GB tạo bằng `tar.exe` đã qua SHA-256 và giải nén; thư mục cài bị chặn ghi nội dung nhưng GUI vẫn khởi động hai lần từ CWD khác và dữ liệu nằm ở vùng người dùng. Docker WebUI đã qua kiểm tra xác thực từ host. `Compress-Archive` thất bại do hết bộ nhớ với thư mục gói 6,38 GB nên workflow đã chuyển sang `tar.exe`.

G3c vẫn mở: workflow `Build Windows Candidate` chưa có run trên runner Windows sạch. Ngày 2026-10-06, current candidate `dist/sp/sp.exe` (SHA-256 `A4C7D607B80C15CF04A023B94BA32A2CF4E31BA8F39B2BDBBA889F79B8B18F25`) đã hoàn tất luồng provider thật: faster-whisper `tiny` STT, Microsoft fallback sau Google HTTP 429, Edge-TTS 1/1 và MP4 H.264/AAC phụ đề cứng với chữ tiếng Việt nhìn thấy trong decoded frame. `main` hiện theo dõi `origin/main`; phần còn thiếu là clean-runner/release artifact gate. Giữ phiên bản sản phẩm 4.14 và chưa tuyên bố phát hành 4.14.1.
