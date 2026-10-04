# PLAN — Ổn định phát hành và nâng cấp pyVideoTrans

Ngày lập: 2026-10-03

Mốc mã được khảo sát: `8cf344fe` (`pyVideoTrans` 4.14)
Nguồn phạm vi: [brainstorm 2026-10-03](brainstorm/session-2026-10-03.md) và [SPEC](SPEC.md)

## Mục tiêu và thứ tự

Đưa sản phẩm tới trạng thái có thể kiểm thử, đóng gói và sử dụng tin cậy; sau đó cải thiện trải nghiệm desktop PySide6. Mỗi gói việc dưới đây phụ thuộc vào cổng nghiệm thu của gói trước. Trong cùng mức ưu tiên, việc ít rủi ro được làm trước để tạo nền kiểm chứng cho việc khó hơn.

**Giả định để lập kế hoạch:** phát hành Windows desktop trước; CLI vẫn hoạt động; WebUI chỉ dùng nội bộ cho tới khi có kiểm soát truy cập; giao diện mới lấy cảm hứng từ luồng làm việc CapCap nhưng giữ PySide6 và bộ xử lý hiện tại. Timeline nhiều lớp là quyết định riêng ở Phase 5. Chưa chọn Remotion làm renderer.

| Ưu tiên | Phase | Kết quả phải đạt |
| --- | --- | --- |
| P0 | 1. Khóa nền kiểm chứng | Test hiện hành chạy được trên Python mục tiêu; lỗi thật và test cũ được phân biệt |
| P0 | 2. Chặn rủi ro dữ liệu và truy cập | Không diễn giải phản hồi ngoài thành mã; TLS được kiểm tra; WebUI an toàn theo chế độ sử dụng |
| P0 | 3. Runtime và bản đóng gói | Có Python còn được hỗ trợ, build Windows tái lập, kiểm tra đầu cuối thành công |
| P1 | 4. Giao diện theo quy trình | Luồng chuẩn bị → chép lời → dịch → lồng tiếng → xem trước/xuất rõ ràng |
| P2 | 5. Timeline có điều kiện | Chỉ khởi động khi người dùng chốt nhu cầu biên tập nhiều lớp |

## Công việc tuần tự

### Phase 1 — Khóa nền kiểm chứng

**1.1. Thiết lập môi trường kiểm thử có thể lặp lại — dễ, P0; SPEC REL-01**

- Xác định Python hiện được khóa ở `>=3.10,<3.11`, phiên bản `uv`, cách cài từ `uv.lock`, FFmpeg và bộ fixture ngắn không cần khóa API.
- Thêm hướng dẫn chạy test và smoke test cho Windows vào tài liệu phát triển; chạy `uv lock --check` và `uv run --locked --group dev pytest -q` trên Python đúng phiên bản.
- Ghi kết quả ban đầu và phân loại test unit, integration, GPU/API. Không dùng kết quả trên Python 3.14 để kết luận tính tương thích 3.10.
- **Cổng:** một máy/runner sạch tái hiện được môi trường và xuất báo cáo test đầy đủ.

**1.2. Sửa test cũ và lỗi cấu hình đã quan sát — dễ đến vừa, P0; SPEC REL-01, DOC-01**

- Sửa import cũ trong `tests/test_custom_api_url.py`, `tests/test_job_helpers.py`, `tests/test_winform_split.py`; đối chiếu hợp đồng thực tế trước khi sửa kỳ vọng trong `tests/test_taskcfg.py`.
- Sửa lỗi ứng dụng nếu test chứng minh hợp đồng mong muốn bị phá; chỉ sửa test nếu hành vi mới đã được xác nhận. Bổ sung test cho parser phụ đề và nhánh job đang thay đổi.
- Đồng bộ phiên bản CLI (`cli.py` đang in 4.03) với phiên bản dự án 4.14; cập nhật chỉ dẫn `--extra dotnet` và `--all-extra` không khớp manifest, cùng bản kiến trúc 4.13.
- **Cổng:** `pytest -q` không lỗi thu thập và không test lỗi trên môi trường chuẩn; CLI trả đúng phiên bản; tài liệu cài đặt dùng lệnh tồn tại.

### Phase 2 — Chặn rủi ro dữ liệu và truy cập

**2.1. Xử lý phản hồi API như dữ liệu — vừa, P0; SPEC SEC-01**

- Tại `videotrans/recognition/_recognapi.py`, bỏ `eval` đối với phản hồi VibeVoice; giữ parser JSON và fallback dữ liệu literal nếu thật sự cần, kiểm tra kiểu, trường và giới hạn kích thước/số đoạn.
- Thêm test với dữ liệu hợp lệ, sai cấu trúc và chuỗi có cú pháp thực thi; kết quả sai phải báo lỗi hoặc bỏ đoạn an toàn, không chạy biểu thức.
- **Cổng:** không còn `eval` trên dữ liệu từ API; các trường hợp trên có test đạt.

**2.2. Khôi phục TLS cho API và tải mô hình — vừa, P0; SPEC SEC-02**

- Lập danh mục mọi `verify=False`/`ssl_verify=False`; bật xác minh chứng chỉ cho endpoint từ xa và đường tải mô hình. Nếu có máy chủ tự quản dùng CA riêng, cấu hình CA bundle rõ ràng theo từng endpoint.
- Kiểm tra lỗi chứng chỉ hiển thị được cho người dùng; thêm kiểm tra hash hoặc nguồn tin cậy đối với tệp mô hình/binary tải về khi nguồn cung cấp hỗ trợ.
- **Cổng:** kết nối chứng chỉ hợp lệ hoạt động; chứng chỉ không hợp lệ bị từ chối; không có tắt TLS ngầm ở đường mặc định.

**2.3. Giới hạn WebUI và dữ liệu xuất — vừa, P0 nếu bật WebUI; SPEC SEC-03**

- Đổi host mặc định về `127.0.0.1`. Nếu cấu hình nghe trên LAN/Internet, yêu cầu xác thực và ghi rõ chế độ triển khai.
- Không đưa log ứng dụng vào danh sách file tải về; kiểm tra lại đường dẫn file đầu vào, kết quả và nội dung lỗi để tránh lộ khóa API/đường dẫn nhạy cảm.
- **Cổng:** mặc định chỉ truy cập từ máy cục bộ; chế độ mạng từ chối yêu cầu chưa xác thực; file đầu ra chỉ gồm tạo phẩm của tác vụ.

**2.4. Giữ an toàn cho đầu ra và cache — vừa, P0; SPEC DATA-01**

- Rà soát `clear_cache` trong `videotrans/task/trans_create.py` và thao tác xóa output cũ ở `webui.py`; phân biệt thư mục tạm với tệp xuất mà người dùng cần giữ.
- Thêm kiểm tra đường dẫn đích và test cho chạy lại, dừng giữa chừng, cùng tên video, thư mục đầu ra tùy chọn.
- **Cổng:** chạy lại không xóa dữ liệu ngoài vùng cache/tác vụ đã được xác định; kết quả cũ có chính sách ghi đè rõ ràng.

### Phase 3 — Runtime và bản đóng gói

**Hàng đợi sửa lỗi audit trước phát hành 4.14.1:** thực hiện 3.4 → 3.5 → 3.6 → 3.7 → 3.8 → 3.9, sau đó hoàn tất 3.1 → 3.2 → 3.3. Giữ số task 3.1–3.3 vì đã có công việc và bằng chứng cục bộ; số mới không biểu thị thứ tự thi công. [Kế hoạch sửa lỗi chi tiết](BUGFIX-PLAN.md) ánh xạ 17 phiếu audit hiện tại, điều kiện nghiệm thu và cổng G3a–G3c. 3.4–3.6 là chặn P0; không đóng gói/phát hành khi chúng chưa qua hồi quy. 3.7–3.9 và các việc P1 trong 3.1/3.2 phải hoàn tất trước cổng phát hành.

**3.4. Cấu hình cũ và bí mật Docker — dễ, P0; BUG-012, BUG-014.** Tái hiện file cấu hình thiếu khóa, thêm giá trị mặc định/migration và test; loại bí mật người dùng khỏi build context và xác nhận image không chứa secret mẫu.

**3.5. Bảo toàn cache và đầu ra CLI — vừa, P0; BUG-001, BUG-002.** Chặn xóa ngoài cache quản lý, kể cả symlink; tách đầu ra cho hai video trùng tên và lần chạy lại; test cả chạy tuần tự, đồng thời và hủy.

**3.6. Docker WebUI và đường dẫn ứng dụng đóng gói — vừa đến khó, P0; BUG-003, BUG-004.** Làm lệnh Docker thực sự truy cập được qua cổng và xác thực; kiểm tra GUI đã đóng gói từ CWD khác với thư mục cài chỉ đọc, ghi dữ liệu ở vùng người dùng.

**3.7. CA tùy chỉnh và quyền sở hữu FFmpeg — vừa, P1; BUG-006, BUG-005.** Giữ cấu hình CA hợp lệ; đóng GUI chỉ dừng FFmpeg do ứng dụng tạo.

**3.8. Toàn vẹn và tải đồng thời mô hình — vừa đến khó, P1; BUG-015, BUG-013.** Kiểm tra tệp cache bằng metadata tin cậy và ghi nguyên tử; bỏ sửa hàm Hugging Face toàn cục gây race.

**3.9. Ngôn ngữ và test có ràng buộc — vừa, P1/P2; BUG-008, BUG-010, ENH-001.** Chuyển mã ngôn ngữ lưu trước đây sang giá trị UI hợp lệ; `--lang` chọn đúng locale; test gọi mã thật và kiểm tra lỗi thực.

**3.1. Chọn Python còn được hỗ trợ bằng ma trận tương thích — khó, P0 trước phát hành công khai; SPEC ENV-01**

- Thử các phiên bản Python còn được hỗ trợ với PySide6, PyTorch/CUDA, `ctranslate2`, `onnxruntime`, thư viện TTS/ASR và PyInstaller. Chọn phiên bản cao nhất vượt qua bộ smoke cốt lõi; không nâng tất cả phụ thuộc một lần.
- Chia phụ thuộc thành lõi desktop, WebUI, và các kênh/mô hình tùy chọn. Khóa lại phiên bản và kiểm tra cài CPU trước, CUDA sau.
- **Cổng:** môi trường sạch cài được từ lockfile trên Python được hỗ trợ; test và smoke đạt trên Windows CPU; đường GPU được xác nhận trên máy GPU.

**3.2. Sửa pipeline đóng gói — vừa đến khó, P0; SPEC PKG-01**

- Thay workflow `.github/workflows/main.yml` đang tham chiếu `sp.spec` và `requirements-win-gpu.txt` không có trong repo. Tạo spec được theo dõi trong Git hoặc chuyển workflow sang lệnh PyInstaller có đủ data, binary và hidden imports.
- CI chạy test trước build; dùng phiên bản PyInstaller thống nhất với manifest; tạo gói CPU Windows trước, gói GPU sau; ghi version và hash artifact. Kiểm tra FFmpeg, font, icon, cấu hình mặc định và đường ghi dữ liệu khi chạy từ gói.
- Với cửa sổ nạp bằng `importlib` từ menu/sidebar, kiểm tra mọi module trong artifact và thực sự mở từng mục sidebar. BUG-016 cho thấy test chỉ tạo QAction không phát hiện đường mở cửa sổ bị thiếu.
- **Cổng:** build trên runner sạch, mở GUI, xử lý fixture ngắn, đóng/mở lại được; artifact tải về và checksum được kiểm tra.

**3.3. Cổng phát hành — khó, P0; SPEC PKG-01, DOC-01**

- Trên gói thực tế: chạy STT → SRT, dịch phụ đề, TTS, ghép MP4; thử lỗi API, mất mạng, hủy tác vụ, CPU và GPU khi có phần cứng.
- Ghi giới hạn đã biết, bản quyền phụ thuộc/binary đi kèm, hướng dẫn cài và changelog. Chỉ đánh dấu bản phát hành khi các cổng 1–3 đạt.
- **Cổng:** checklist phát hành có bằng chứng test, log build, video fixture và kết quả đầu ra.

### Phase 4 — Giao diện theo quy trình

**Lát cắt desktop được duyệt 2026-10-04:** bổ sung `vi_VN`, splash Qt mới, trang chủ “Xưởng Video” với lối vào không gian làm việc và bốn công cụ nhanh. Kiểm tra nguồn, bản đóng gói, sidebar và menu động là cổng nghiệm thu riêng của lát cắt này. Tên hiển thị đang là tên tạm. Thiết kế lại toàn bộ màn hình xử lý năm bước ở 4.1–4.3 vẫn là việc tiếp theo; không đánh dấu Phase 4 hoàn tất chỉ vì trang chủ mới đã hoạt động.

**Bằng chứng cục bộ:** 546 test nguồn đạt; candidate `pytransvideo-vietnamese-ui-20261004` đạt smoke tiếng Việt/trang chủ, 5/5 sidebar, 71/71 menu động, CLI/SRT/media mẫu và khởi động GUI 15 giây từ thư mục khác. Chưa thực hiện kiểm thử nhà cung cấp API, GPU và runner Windows sạch cho cổng phát hành 3.3.

**4.1. Chốt hướng thiết kế bằng mẫu màn hình — vừa, P1; SPEC UI-01, UI-03**

- Dùng PySide6. Thiết kế một cửa sổ chính với các bước chuẩn bị, chép lời, dịch, lồng tiếng, xem trước/xuất; giữ menu công cụ và cấu hình kênh nâng cao.
- Kiểm chứng màn hình 1280×720 và 1920×1080, tiếng Việt/Anh, trạng thái rỗng/đang chạy/lỗi/xong, điều hướng bàn phím.
- **Cổng:** danh sách màn hình, trạng thái và tương tác được duyệt trước khi thay `videotrans/ui/en.py`.

**4.2. Tách trạng thái quy trình khỏi widget — vừa đến khó, P1; SPEC UI-02, UI-04**

- Đặt bộ chuyển đổi giữa `SignMsg`/task state hiện có và view state; widget không trực tiếp quyết định nghiệp vụ hay tạo đường dẫn output.
- Giữ API CLI và task hiện tại; đưa phần sửa phụ đề, gán vai và xem trước hiện có vào luồng mới theo từng lát cắt.
- **Cổng:** tác vụ một video và nhiều video chạy qua GUI mới; trạng thái pause/retry/error hiển thị nhất quán.

**4.3. Hoàn thiện UI và hồi quy — khó, P1**

- Áp dụng theme, khoảng cách, thứ bậc nút, bảng phụ đề, vùng video và tiến độ; thêm test cho logic view state và smoke GUI thủ công trên bản đóng gói.
- **Cổng:** người mới hoàn thành video mẫu mà không cần đi tìm hộp thoại theo từng bước; không làm mất chức năng CLI/WebUI.

### Phase 5 — Timeline có điều kiện

**5.1. Quyết định phạm vi — P2.** Chỉ mở Phase này khi người dùng cần chỉnh thời điểm phụ đề/giọng và nhiều lớp media trong cùng dự án. Nếu nhu cầu chỉ là sửa SRT và xem trước, Phase 4 là điểm dừng.

**5.2. Thiết kế mô hình dự án, lưu/mở, undo/redo — khó.** Định nghĩa track, clip, mốc thời gian, tài nguyên nguồn và phiên bản file dự án trước khi làm widget timeline.

**5.3. Đồng bộ playhead, preview và xuất video — rất khó.** Kiểm thử seek, waveform/thumbnail cache, xuất FFmpeg từ cùng một trạng thái dự án. Chỉ mở rộng sang blur/logo/mask sau khi phụ đề và âm thanh đạt độ chính xác.

## Quy tắc thực hiện

- Mỗi gói có thay đổi mã cần test chứng minh hành vi và có bằng chứng cổng nghiệm thu trước khi sang gói tiếp theo.
- Ưu tiên sửa lỗi đã xác nhận; phát hiện mới được xếp theo tác động tới dữ liệu, an toàn, khả năng đóng gói rồi mới tới giao diện.
- Không gộp di chuyển Python, thay kiến trúc UI và thêm timeline trong một đợt thay đổi.
- Các quyết định còn mở ở brainstorm được chốt trước Phase 4 và Phase 5; Phase 1–3 có thể thực hiện ngay theo bằng chứng hiện tại.

## Nguồn kỹ thuật đã đối chiếu

- [uv: locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) — dùng lockfile và `--locked` để kiểm tra tính tái lập.
- [PyInstaller: spec files](https://pyinstaller.org/en/latest/spec-files.html) — spec là đầu vào build cho data và binary đi kèm.
- [Qt for Python: QMediaPlayer](https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QMediaPlayer.html) — nền xem trước hiện có.
- [Gradio: sharing and authentication](https://gradio.app/guides/sharing-your-app) — truy cập mạng và xác thực.
- [Python 3.10 final security release](https://www.python.org/downloads/release/python-31022/) — lý do cần di chuyển runtime trước phát hành dài hạn.
