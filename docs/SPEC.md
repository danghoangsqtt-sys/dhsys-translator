# SPEC — Yêu cầu và nghiệm thu cho kế hoạch nâng cấp pyVideoTrans

Ngày lập: 2026-10-03

Trạng thái: Đặc tả triển khai Phase 1–3; lát cắt trang chủ/Việt hóa Phase 4 được duyệt ngày 2026-10-04; luồng biên tập đầy đủ và Phase 5 còn theo kế hoạch
Kế hoạch thứ tự: [PLAN](PLAN.md)

## 1. Phạm vi sản phẩm

pyVideoTrans nhận video/âm thanh, tạo phụ đề, dịch, tạo tiếng nói và xuất media; có GUI PySide6, CLI và WebUI. Bản nâng cấp giữ quy trình xử lý trong `videotrans/task`, các adapter trong `videotrans/recognition`, `translator`, `tts`, cùng FFmpeg. Giao diện desktop mới tổ chức lại cách người dùng truy cập các bước này. Hợp đồng CLI và định dạng đầu ra được coi là tương thích, trừ thay đổi được ghi rõ trong changelog.

### Ràng buộc và quyết định còn mở

- **Mặc định:** Windows desktop là mục tiêu đóng gói đầu tiên; macOS/Linux và WebUI vẫn có thể chạy từ nguồn nhưng chưa có cổng build phát hành mới.
- **Giao diện:** PySide6. Đợt đầu Phase 4 gồm splash, trang chủ desktop và tiếng Việt; luồng biên tập theo quy trình vẫn cần nghiệm thu riêng. Chưa chọn React/Remotion.
- **Timeline:** chỉ là Phase 5 có điều kiện. Chưa có yêu cầu để sao chép toàn bộ chức năng CapCap hoặc Remotion.
- **Python:** hiện khóa 3.10; phiên bản thay thế được chọn qua ma trận tương thích, không ấn định trước khi thử mô hình và gói đóng.

## 2. Hợp đồng chức năng và phi chức năng

### REL-01 — Test là cổng phát hành

**Hiện trạng:** test toàn bộ dừng ở bước thu thập vì 4 import lỗi; nhóm test cấu hình chạy riêng có 39 đạt, 3 lỗi trên Python 3.14 không được hỗ trợ. Các import cũ nằm ở `tests/test_custom_api_url.py`, `test_job_helpers.py`, `test_winform_split.py`; kỳ vọng sai hoặc lỗi mã nằm ở `test_taskcfg.py`.

**Yêu cầu:** test unit không đòi GPU, khóa dịch vụ hay mạng; integration test đánh dấu riêng. Sửa import và kỳ vọng bằng hợp đồng dữ liệu của `TaskCfg*`/API hiện tại; không xóa test để làm xanh CI. CI bắt buộc chạy unit test trên runtime được chọn, thất bại thì không build phát hành.

**Nghiệm thu:** `pytest -q` hoàn tất thu thập; tất cả test bắt buộc đạt; mỗi lỗi cũ có commit sửa hoặc quyết định thay đổi hợp đồng có giải thích.

### SEC-01 — Phân tích phản hồi ASR an toàn

**Hiện trạng:** `videotrans/recognition/_recognapi.py` thử `json.loads`, `ast.literal_eval`, rồi `eval` với kết quả bên ngoài.

**Yêu cầu:** chỉ chấp nhận danh sách đoạn có `Start`, `End`, `Content` và `Speaker` tùy chọn theo kiểu được khai báo; giới hạn kích thước phản hồi và số đoạn; từ chối thời gian âm, NaN, `End < Start`. Không thực thi biểu thức từ phản hồi. Giữ hành vi thành công đối với mẫu VibeVoice hợp lệ.

**Nghiệm thu:** test chứa chuỗi gọi hàm/biểu thức không tạo tác dụng phụ; phản hồi sai sinh lỗi có thể chẩn đoán; mẫu hợp lệ xuất SRT giống trước.

### SEC-02 — TLS và tệp tải xuống

**Hiện trạng:** các adapter và `videotrans/util/help_down.py` dùng `verify=False`/`ssl_verify=False`.

**Yêu cầu:** HTTPS mặc định xác minh chứng chỉ; CA tùy chỉnh chỉ được cấu hình tường minh cho endpoint tương ứng. Lỗi TLS không bị biến thành thông báo chung che mất nguyên nhân. Tệp tải về được kiểm tra kích thước/hash nếu có metadata đáng tin cậy trước khi giải nén/sử dụng.

**Nghiệm thu:** server chứng chỉ hợp lệ hoạt động; chứng chỉ giả hoặc sai tên miền bị từ chối; tìm kiếm tĩnh không thấy TLS bị tắt ở nhánh mặc định.

### SEC-03 — WebUI và dữ liệu người dùng

**Hiện trạng:** `webui.py` mặc định host `0.0.0.0`, gọi `launch` không có xác thực, và thêm log hằng ngày vào file tải về.

**Yêu cầu:** mặc định loopback. Khi người vận hành chọn host không phải loopback, phải cung cấp xác thực hoặc ứng dụng từ chối khởi động với thông báo rõ; hướng dẫn đặt reverse proxy/TLS cho triển khai từ xa. Danh sách tải về chỉ gồm kết quả của tác vụ; dữ liệu log, cấu hình và khóa API không là output. Phản hồi lỗi không đưa secret lên UI.

**Nghiệm thu:** truy cập từ máy khác thất bại ở chế độ mặc định; chế độ mạng chặn người chưa xác thực; output list không có log/config.

### DATA-01 — Chính sách cache và ghi đè

**Hiện trạng:** `TransCreate.__post_init__` có thể xóa `target_dir` khi `clear_cache`; WebUI xóa MP4/MKV cũ trong output cùng tên trước khi chạy.

**Yêu cầu:** cache phải có thư mục được ứng dụng quản lý; không xóa ngoài thư mục đó bằng đường dẫn do người dùng cung cấp. Output đã hoàn thành được giữ hoặc ghi đè qua chính sách rõ ràng. Tác vụ bị hủy/lỗi không xóa bản xuất đã hoàn thành trước đó.

**Nghiệm thu:** test đường dẫn tùy chọn, chạy lại, trùng tên và hủy tác vụ; so sánh danh sách file trước/sau để xác nhận dữ liệu ngoài tác vụ không bị xóa.

### ENV-01 — Runtime và phụ thuộc tái lập

**Yêu cầu:** chọn một bản Python còn được hỗ trợ mà các chức năng lõi và packaging đều chạy được. Ma trận tối thiểu: PySide6, FFmpeg, torch/torchaudio CPU và CUDA, Faster-Whisper/CTranslate2, một kênh dịch, một kênh TTS, PyInstaller. Giữ các kênh ít dùng ở nhóm tùy chọn nếu chúng chặn nâng runtime; nêu giới hạn rõ trong tài liệu. Mọi thay đổi manifest phải cập nhật `uv.lock` và vượt `uv lock --check`.

**Nghiệm thu:** cài sạch từ lockfile, chạy test, CLI help/version, GUI mở, tạo SRT và MP4 fixture ngắn trên Windows CPU; GPU kiểm tra trên phần cứng phù hợp.

### PKG-01 — Gói Windows có thể sử dụng

**Yêu cầu:** workflow build chỉ tham chiếu tệp có trong Git; phiên bản công cụ đồng nhất; bundle FFmpeg, icon, font và tài nguyên Qt cần thiết; không bundle secret, cache, model đã tải hoặc output cá nhân. Artifact có tên kèm version, checksum và hướng dẫn chạy lần đầu.

**Nghiệm thu:** runner sạch tạo artifact; giải nén ở đường dẫn mới và chạy `sp.exe` không cần môi trường Python; smoke tạo output và khởi động lần hai thành công. Bản CPU là cổng bắt buộc; GPU là cổng riêng.

### DOC-01 — Một nguồn thông tin phiên bản và cài đặt

**Yêu cầu:** CLI `--version`, README, tài liệu kiến trúc và ví dụ `uv sync` khớp manifest; không hướng dẫn extra không có trong `pyproject.toml`. Mọi bản phát hành ghi changelog và yêu cầu máy tối thiểu.

**Nghiệm thu:** kiểm tra tự động hoặc checklist đối chiếu các phiên bản, extra và lệnh cài trong tài liệu.

### FIX-01 — Khởi động và nguồn bí mật (BUG-012, BUG-014)

Thiếu hoặc sai kiểu trường trong `params.json` cũ dùng giá trị mặc định hợp lệ và giữ các lựa chọn còn hợp lệ; quá trình khởi động không ném `KeyError`. Docker build context/image/layers không chứa `.env`, cấu hình người dùng, khóa hay output. Nghiệm thu bằng cấu hình cũ thực tế và secret mẫu được quét trong image.

### FIX-02 — Bảo toàn dữ liệu (BUG-001, BUG-002)

Mọi đường xóa cache phải xác nhận nằm trong thư mục task được quản lý, không đi qua symlink và không xóa chính root. Hai đầu vào cùng basename có đầu ra riêng hoặc chính sách va chạm công khai; chạy lại không ghi đè âm thầm. Nghiệm thu bằng so sánh nội dung file trước/sau trong các ca thành công, lỗi, hủy và chạy đồng thời.

### FIX-03 — Chạy được từ container và gói desktop (BUG-003, BUG-004, BUG-007)

WebUI trong Docker nghe trên interface được publish khi có xác thực, tài liệu có lệnh chạy dùng được. App frozen đọc tài nguyên theo bundle và ghi cache/config/output ở vùng người dùng, chạy từ CWD khác và thư mục cài chỉ đọc. Gói phải chứa provider/dialog import động. Nghiệm thu trên container và artifact giải nén thật, gồm một provider và một dialog động.

### FIX-04 — Vòng đời và mạng (BUG-005, BUG-006, BUG-013, BUG-015)

Ứng dụng chỉ dừng FFmpeg do chính nó tạo. CA bundle được người dùng cấu hình hợp lệ phải được giữ nguyên; CA sai báo lỗi rõ. Tải mô hình đồng thời không thay đổi hàm toàn cục gây tranh chấp; tệp hỏng/thiếu phải tải lại qua tệp tạm và xác nhận hash/size/định dạng theo metadata đáng tin cậy. Nghiệm thu bằng test song song và kiểm tra tiến trình/tệp thật.

### FIX-05 — Tương thích ngôn ngữ và nguồn phát hành (BUG-008, BUG-009, BUG-010, BUG-011, ENH-001)

Cấu hình ngôn ngữ WebUI cũ ánh xạ tới lựa chọn hợp lệ; `--lang en/zh` chọn locale tương ứng độc lập với hệ điều hành. Ma trận Python phân biệt core và extras; nguồn binary/model dùng bản bất biến hoặc checksum xác minh. README, hướng dẫn phát triển, task state, HANDOFF và manifest mô tả cùng một runtime đã kiểm chứng. Test GUI/CLI phải gọi mã sản phẩm thay vì chỉ kiểm tra callable hay khẳng định luôn đúng. Nghiệm thu bằng cài sạch, test hành vi và smoke artifact theo [kế hoạch sửa lỗi](BUGFIX-PLAN.md).

## 3. Giao diện desktop — Phase 4

### UI-01 — Luồng người dùng

Một tác vụ đơn hiển thị 5 vùng/bước chính: **Chuẩn bị**, **Chép lời**, **Dịch**, **Lồng tiếng**, **Xem trước & Xuất**. Bước không áp dụng được bỏ qua có giải thích; ví dụ tác vụ chỉ tạo SRT không buộc người dùng chọn TTS. Cấu hình provider nâng cao nằm trong bảng phụ để màn hình chính chỉ giữ lựa chọn quan trọng.

### UI-02 — Trạng thái và sửa lỗi

Mỗi bước có trạng thái `chưa bắt đầu / đang chạy / cần người dùng sửa / thành công / lỗi / đã hủy`. UI lấy trạng thái từ sự kiện tác vụ hiện có (`SignMsg` và các worker), không tự suy đoán từ việc file có tồn tại. Một lỗi hiển thị bước, nguyên nhân có thể đọc được, hành động thử lại hoặc mở log. Khi sửa phụ đề hay gán giọng, bản xem trước phát đúng đoạn được chọn.

### UI-03 — Bố cục và khả dụng

Tại 1280×720 không cắt nút hành động chính; tại 1920×1080 vùng video và bảng phụ đề có thể mở rộng. Điều hướng bằng bàn phím tới các bước và nút chính; nhãn tiếng Việt/Anh không bị cắt; theme có độ tương phản đủ đọc. Giữ chức năng batch nhưng phân biệt rõ nó với luồng sửa từng video.

### UI-04 — Ranh giới triển khai

Thay đổi tập trung ở `videotrans/ui/`, `videotrans/mainwin/` và các component liên quan. Tạo lớp ánh xạ trạng thái task → view để tránh trộn xử lý video vào widget. Không thay hợp đồng CLI, các adapter AI hay định dạng SRT/MP4 chỉ để đạt bố cục mới. Demo UI phải chạy với fixture không cần khóa API.

**Nghiệm thu Phase 4:** người dùng mở một video, hoàn thành từng bước, sửa một dòng phụ đề, nghe/xem đoạn đó, xuất và mở file kết quả; batch vẫn chạy; cổng Phase 1–3 tiếp tục đạt.

## 4. Timeline — Phase 5, điều kiện khởi động

Chỉ chốt khi đã xác nhận thao tác cần làm trên timeline. Phiên bản đầu nếu được chọn chỉ gồm track video tham chiếu, phụ đề và tiếng nói; hỗ trợ kéo/sửa thời gian, phát tại playhead, undo/redo, lưu/mở dự án có version. Waveform và thumbnail được cache nền. Preview và export phải đọc cùng mô hình dự án; test so khớp các mốc phụ đề/âm thanh trong file xuất với dự án đã lưu. Logo, blur, mask, hiệu ứng và tích hợp Remotion là yêu cầu riêng sau cổng này.

## 5. Bằng chứng và cổng hoàn thành

| Cổng | Bằng chứng tối thiểu |
| --- | --- |
| G1 sau Phase 1 | Log cài môi trường sạch, log pytest đầy đủ, danh sách test integration cần dịch vụ ngoài |
| G2 sau Phase 2 | Test đầu vào ASR độc hại/sai cấu trúc, kiểm tra TLS, kiểm tra truy cập WebUI và test bảo toàn output |
| G3 sau Phase 3 | Ma trận Python/phụ thuộc, log CI, checksum gói, bản ghi smoke GUI/CLI và MP4/SRT fixture |
| G4 sau Phase 4 | Mẫu màn hình được chốt, kiểm tra 2 cỡ màn hình, bài thử 1 video và batch, hồi quy G1–G3 |
| G5 nếu có Phase 5 | Tệp dự án lưu/mở, undo/redo, seek/preview và so khớp video xuất |

Không đánh dấu cổng đạt chỉ bằng test có mock: G3–G5 cần chạy với gói và media thực.


### UI-05 ? Light visual system

The desktop application, launch screen, home page, main workspace, menus and ordinary dialogs use a light interface. White is the base surface, neutral gray separates regions, and `#14452F` is the primary action and focus color. Text and disabled states must remain legible, including on the selected menu item. The product credit `DHSYSTEM.SYS` is visible on the home page and workspace shell. This requirement changes style only; it does not change task execution, saved settings, output paths, API adapters, CLI behavior or file formats.

### UI-06 ? Feature parity and routes

Every pre-existing QAction remains instantiated and reachable from the menu bar. The workspace shell may expose shortcuts only by triggering those same QAction instances. Translate SRT, Multiple speakers, and Merge video/audio/SRT remain available. Dynamic provider/dialog routes and all advanced settings remain reachable. No action is duplicated with a separate business implementation.

### UI-07 ? Workspace hierarchy

The desktop workspace has a persistent identity/navigation area, a clear page title, a visually primary start control, and the original configuration, subtitle and queue controls. At 1280?720, users can reach the primary action and scrolling controls without hidden modal navigation. At 1920?1080, the content uses the extra space without changing widget semantics. The original top menu remains the full tool catalog.

**Acceptance for the approved light-layout slice:** the light theme and shell load in the packaged source path; original actions are still used for all shortcuts; focused Qt tests plus the full Python 3.12 suite pass; visual smoke covers 1280?720 and 1920?1080. This slice does not close Phase 3 release gates.


### UI-08 ? Packaged light interface integrity

The Windows candidate built from tracked `sp.spec` must bundle `videotrans/styles/light.qss` and load it through `sp.py`. Its frozen smoke runs from outside the installation directory and confirms that the light stylesheet resolves alongside the existing style, icon, FFmpeg, dynamic provider/dialog, CLI and fixture-media checks. Passing this local candidate gate does not claim clean-runner, live-provider or release completion.
