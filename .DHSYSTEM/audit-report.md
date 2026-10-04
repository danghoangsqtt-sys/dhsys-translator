# DH-AUDIT — rà soát lỗi chuyên sâu pyVideoTrans

## Audit sidebar Windows — 2026-10-04

### Tier 1 — trạng thái: cảnh báo

Task 3.2 từng được ghi “verified locally” sau smoke một dialog `chatgpt`, nhưng người dùng tái hiện lỗi ở cả năm mục sidebar trên artifact thật. Bản build mới đã mở được 5/5 mục sidebar và 72/72 menu động; task 3.2 được xác minh cục bộ. Phase 3 và bản vá 4.14.1 vẫn chưa hoàn tất vì còn cổng runner sạch và luồng media đầy đủ.

### Tier 2 — tài liệu: cảnh báo

`CHANGELOG.md` từng mô tả `jaraco.text`, ZIP smoke và Docker như các cổng chưa kiểm tra, dù chúng đã qua cục bộ. Đã cập nhật phạm vi kiểm chứng và BUG-016. Phiên bản 4.14 trong README/manifest nhất quán; các TODO trong tài liệu mở rộng là ví dụ, không phải URL placeholder.

### Tier 3 — PyInstaller/Qt: lỗi cao, chặn phát hành

`videotrans/ui/menu_list.py` khai báo năm hành động trái `fn_recogn`, `fn_peiyin`, `fn_fanyisrt`, `fn_peiyinrole`, `fn_vas`. `_setup_menus.py` nối hành động vào `get_win(name)`, còn `winform/__init__.py` nạp module bằng `importlib`. Spec cũ chỉ khai báo động cho `chatgpt`. `scripts/smoke_sidebar.py` trên executable cũ thất bại **5/5** với `ModuleNotFoundError: videotrans.winform.fn_*`; chạy từ source đạt **5/5**. Bộ test 540 bài và smoke cũ không bấm các hành động này nên không phát hiện lỗi. Sau khi sửa năm mục trái, kiểm tra mở rộng `scripts/smoke_dynamic_menus.py` cho thấy source import **72/72** menu động, còn executable chỉ **7/72**; 65 menu cấu hình/công cụ/trợ giúp cũng thiếu module. `sp.spec` hiện suy ra 139 module cần đóng gói từ chính khai báo menu. Bản Windows 3.12 mới mở được **5/5** cửa sổ sidebar và **72/72** cửa sổ menu động từ thư mục bàn giao; GUI khởi động, provider/dialog, CLI, SRT và MP4 mẫu cũng qua smoke. Python 3.12 đạt **540/540** test. Cổng runner sạch và luồng media dùng provider thật vẫn mở.

Guardrail cho `dh-auto`: mỗi hành động GUI nạp động phải có module trong artifact và một smoke gọi đúng đường `get_win` từ executable đã giải nén; test chỉ kiểm tra QAction tồn tại không đủ. Tier 4 không áp dụng vì đây là repository sản phẩm.

## Audit tiếp nối — 2026-10-04

Mốc đối chiếu: `HEAD=8cf344fe` trên `main` (trùng `origin/main`); lịch sử Git gần nhất kết thúc ngày 2026-09-30. Toàn bộ tiến độ Phase 1–3 được ghi trong working tree chưa commit, không có commit/tag `dh-p*-complete` cho phần việc này. Trạng thái sản phẩm vẫn là 4.14; 4.14.1 chỉ là bản vá dự kiến.

### Tier 1 — trạng thái: cảnh báo

- `TRACKER.md` và `HANDOFF.json` cùng chỉ task 3.3, nhưng `TRACKER.md` ghi 3.2 “verified locally” còn `phases/3/PHASE-STATE.md` ghi “in_progress (review correction)”; `ROADMAP.md` vẫn ghi Phase 3 “repair plan ready, execution pending” dù các task 3.4–3.9 đã có kết quả kiểm chứng cục bộ. Cần đồng bộ nhãn trạng thái và tách rõ cổng local, artifact và Git.
- 3.6 và 3.3 còn mở đúng với cổng nghiệm thu. Phases 1–2 chỉ `verified_local`, nên chưa có tag hoàn thành là nhất quán. Mọi phiếu BUG-001–015 và ENH-001 vẫn `open`; nhiều phiếu đã có kiểm chứng cục bộ nhưng chưa được đóng theo cổng tương ứng.
- `sp.spec`, `version.txt`, `docs/PLAN.md` và `.DHSYSTEM/TRACKER.md` chưa được Git theo dõi (`git ls-files --error-unmatch` thất bại). Checkout sạch tại `HEAD` không có các đầu vào mà workflow ứng viên cần. `origin` vẫn trỏ tới upstream `jianchang512/pyvideotrans`.

### Tier 2 — tài liệu: cảnh báo

- `docs/runtime-matrix.md` vẫn mở đầu “release runner remains on Python 3.10” và bảng ghi 3.10 là “Default build runtime”, trong khi chính tài liệu, `docs/dev-setup.md`, `TRACKER.md` và workflow đã chọn Python 3.12.13. `docs/faq.md` cũng nói Windows đóng gói vẫn theo 3.10. Đây là drift trong phần hướng dẫn hiện hành; ghi tiếp vào BUG-011.
- `docs/review-nemotron-2026-10-04.md` mô tả trạng thái trước các bước sửa tiếp theo (3.10 build, 518 test, `wetext` cp310), nhưng không đánh dấu rõ là ảnh chụp lịch sử. Giữ làm biên bản lịch sử và thêm chỉ dẫn tới ma trận hiện hành khi sửa tài liệu.
- Manifest và CLI vẫn cùng phiên bản 4.14; `CHANGELOG.md` có mục Unreleased. Không thấy URL mẫu `your-org`/`YOUR_USERNAME` trong `docs/`. Các TODO trong tài liệu mở rộng là vị trí minh họa mã, không tính là lỗi dự án.

### Tier 3 — Python, Docker, đóng gói: đạt ở mức test nguồn; chặn phát hành

- Chạy lại Python 3.10.19 bằng `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=<thư mục tạm mới>`: **540 passed in 18.89s**. `uv lock --check --offline`: **Resolved 424 packages**, exit 0. `git diff --check`: exit 0. Quét adapter Python không thấy `verify=False`/`ssl_verify=False` còn lại; `eval()` tìm được là lời gọi phương thức model của PyTorch, không phải built-in xử lý phản hồi API.
- `docker version` không kết nối được `dockerDesktopLinuxEngine`, nên BUG-003 chưa có bằng chứng host-port/auth trên container. `dist/sp/sp.exe` và `ffmpeg/ffmpeg.exe` không có tại thời điểm audit; kiểm chứng artifact được ghi trước đó không thể lặp lại trên workspace hiện tại. Không có log runner sạch, provider/dialog thực thi trong artifact, SRT/MP4 từ gói, checksum ZIP hoặc smoke từ thư mục cài read-only. BUG-004, BUG-007, BUG-009 và cổng 3.3 tiếp tục mở.
- Workflow hiện chỉ chạy unit tests, kiểm tra layout, nén và tải artifact; nó không thực thi GUI/provider/media smoke trên artifact đã giải nén. Vì vậy workflow thành công chưa đủ để tuyên bố đạt G3c. Không tăng version hoặc phát hành 4.14.1 theo bằng chứng hiện có.

### Hướng tiếp tục và guardrails cho `dh-auto`

1. Lưu thay đổi trên một nhánh/fork có quyền ghi; đảm bảo `sp.spec`, `version.txt`, kế hoạch và state được theo dõi trước khi chạy CI. Không đẩy lên upstream khi chưa có quyền/ý định rõ.
2. Đồng bộ `TRACKER`/`ROADMAP`/`PHASE-STATE` và tài liệu runtime theo Python 3.12.13 candidate; giữ biên bản 2026-10-04 như lịch sử có nhãn.
3. Chạy build Windows sạch và smoke từ ZIP đã giải nén: GUI từ CWD khác và thư mục cài read-only, khởi động lần hai, một provider/dialog động, SRT và MP4 ngắn, kiểm tra SHA-256. Chạy Docker host-port/auth smoke khi daemon sẵn có.
4. Chỉ chuyển task/phiếu sang PASS khi bằng chứng của chính cổng nghiệm thu tồn tại. Giữ 4.14 trong manifest/CLI cho tới khi G3c hoàn chỉnh.

**Tự động sửa:** chưa áp dụng. Các vấn đề trên đã có phiếu BUG-003/004/007/009/011 và task 3.3; không tạo phiếu trùng. Tier 4 không áp dụng cho repository sản phẩm này.

## Rà soát tăng dần trong task 3.3 — 2026-10-04

- **Tier 1/2:** README, Chinese README, dev setup, matrix, task contract, tracker and handoff now agree that source core 3.10–3.12 was verified and that candidate packaging uses 3.12.13. Version remains 4.14; 4.14.1 is not released.
- **Tier 3:** onedir artifact starts twice in isolated offscreen mode; 97 focused tests, lock verification, YAML parsing and whitespace checks pass. Docker daemon is unavailable, so container verification cannot be claimed. Clean runner, dynamic provider/dialog execution inside artifact, packaged SRT/MP4 smoke, archive checksum and Git persistence remain release blockers. No new code defect was reproduced within task scope; no further dh-debug repair is applicable.

## Rà soát tăng dần sau task 3.2 — 2026-10-04

- **Tier 3:** Python 3.12.13 builds the onedir artifact after removing the `distutils` exclusion; artifact has resources and starts headlessly with isolated user data. Python 3.10 has reproducible native stack overflow in the torchaudio hook, so workflow uses the tested 3.12 runtime.
- **Open gates:** clean Windows runner, in-artifact dynamic provider/dialog interaction, and real packaged media workflow remain task 3.3. No release is claimed.

## Rà soát tăng dần trong task 3.2 — 2026-10-04

- **Tier 3, blocker:** local PyInstaller 6.16.0/Python 3.10.19 crashes in `python310.dll` (`0xc00000fd`) during the `torchaudio` hook. Disk space was sufficient; smaller explicit dynamic-import coverage and a higher Python recursion limit did not resolve it. No `dist/sp` artifact exists, so extracted GUI/provider/media smoke cannot run.
- **Decision:** task remains in progress. The workflow/spec corrections are retained, but release gating is truthful: reproduce on a clean Windows runner or isolate the hook before accepting BUG-007.

## Rà soát tăng dần sau task 3.1 — 2026-10-04

- **Tier 1:** 3.1 verified locally, chưa PASS vì Git persistence và artifact smoke. TRACKER/HANDOFF chuyển 3.2; 3.6 vẫn mở.
- **Tier 2:** runtime matrix, setup, FAQ, tracker và phase state đã cập nhật theo bằng chứng mới; mặc định build 3.10, mã nguồn 3.10–3.12.
- **Tier 3:** ba môi trường khóa với `wetext` đều cài và qua 540 bài test; `uv lock --check --offline` giải 424 gói; Chatterbox/Perth pin commit. FFmpeg archive SHA-256 khớp GitHub release cố định, tạo được MP4 ngắn có audio/video. Audit thấy chuỗi escape cảnh báo ở `_sttapi.py` và `_srt_parse.py`; dh-debug sửa cú pháp, 42 bài test liên quan đạt trên 3.10 và 3.12, `git diff --check` sạch. Cổng clean runner và packaged media còn mở.


## Rà soát tăng dần sau task 3.9 — 2026-10-04

- **Tier 1:** 3.9 được xác minh cục bộ, chưa PASS vì Git persistence; TRACKER/HANDOFF chuyển 3.1. 3.6 vẫn thiếu Docker container và Windows artifact smoke.
- **Tier 2:** hợp đồng task, yêu cầu, changelog ghi rõ giới hạn packaged GUI/media thuộc 3.3.
- **Tier 3:** 102 bài test tập trung và 540 bài test toàn bộ đạt; Gradio dùng lựa chọn hợp lệ và mã voice locale đúng; desktop `--lang` có hiệu lực trước import; Qt/CLI test chạy hàm thật. `git diff --check` phát hiện dòng trắng cuối file test, đã sửa theo vòng dh-debug; không còn lỗi mới trong phạm vi task.


## Rà soát tăng dần sau task 3.4 — 2026-10-04

- **Tier 1, trạng thái:** TRACKER/PHASE-STATE/HANDOFF cùng chỉ task 3.5; task 3.4 mới verified locally vì working tree chưa commit/push. Không có tag PASS mới.
- **Tier 2, tài liệu:** kế hoạch và changelog ghi đúng “verified locally”; tài liệu Docker chạy thật vẫn cần sửa ở task 3.6, chưa được coi là đã đạt.
- **Tier 3, Python/Docker:** cấu hình cũ `{}` và giá trị sai kiểu đã có hồi quy; 523 test Python 3.10 đạt. Scratch Docker image từ context thật loại dummy `.env`, params/cfg; source ứng dụng vẫn có mặt. Không thấy lỗi sản phẩm mới trong phạm vi task 3.4. Cổng phát hành Windows và kiểm Docker WebUI còn mở ở task sau.
- **Tier 4:** không áp dụng, repo này là sản phẩm Python chứ không phải repo framework DHSYSTEM.

## Rà soát tăng dần sau task 3.5 — 2026-10-04

- **Tier 1:** TRACKER/PHASE-STATE/HANDOFF cùng chỉ task 3.6; task 3.5 verified locally, chưa PASS vì chưa qua Git persistence gate.
- **Tier 2:** CLI help mô tả đúng thư mục gốc và thư mục riêng mỗi lượt; changelog giữ trạng thái local verification.
- **Tier 3:** 88 test tập trung và 528 test Python 3.10 đạt; cache ngoài/root/symlink không bị xóa, `--no-clear-cache` giữ cache, đầu ra trùng tên và chạy đồng thời có thư mục riêng. `compileall` với pycache tạm đạt. Không phát hiện lỗi mới trong phạm vi BUG-001/BUG-002; `dh-debug` không cần sửa thêm.
- **Tier 4:** không áp dụng.

## Rà soát tăng dần trong task 3.6 — 2026-10-04

- **Tier 1:** 3.6 còn `in_progress` vì chưa có container và artifact smoke; TRACKER/HANDOFF chuyển task làm mã kế tiếp sang 3.7 nhưng giữ rõ cổng 3.6 đang mở. Git persistence vẫn chưa đạt.
- **Tier 2:** `docs/webui.md` nay mô tả loopback mặc định, auth bắt buộc trên mạng và mount từng file cấu hình; không còn hướng dẫn mount đè mã nguồn.
- **Tier 3:** 534 test Python 3.10 đạt; frozen import từ CWD khác không tạo file trong install tree. Rà soát tìm thấy nhánh thiếu thư mục user-data `videotrans` và FunASR helper còn dùng root ghi dữ liệu; hai lỗi này đã được sửa trong phiên debug. Docker host-port/auth và Windows artifact read-only smoke chưa đạt vì build còn chạy/chưa chạy.
- **Tier 4:** không áp dụng.

## Rà soát tăng dần sau task 3.7 — 2026-10-04

- **Tier 1:** task 3.7 verified locally; task 3.6 vẫn mở cổng container/artifact; TRACKER/HANDOFF cùng chỉ task 3.8 đang làm. Không đánh dấu PASS vì Git persistence chưa đạt.
- **Tier 2:** changelog giữ phân biệt giữa sửa đổi cục bộ và bản đã phát hành.
- **Tier 3:** CA người dùng được giữ và CA sai báo lỗi có tên biến; `psutil` chỉ chọn FFmpeg hậu duệ của ứng dụng. Smoke thật xác nhận FFmpeg ngoài ứng dụng tiếp tục chạy, FFmpeg thuộc ứng dụng dừng. 7 test tập trung và 539 test Python 3.10 đạt; không tìm thấy lỗi mới trong BUG-005/BUG-006, nên không mở phiên `dh-debug` mới.
- **Tier 4:** không áp dụng.

## Rà soát tăng dần sau task 3.8 — 2026-10-04

- **Tier 1:** task 3.8 verified locally, cổng Git persistence chưa đạt; TRACKER/HANDOFF cùng chỉ task 3.9. Task 3.6 còn mở cổng artifact/container.
- **Tier 2:** changelog mô tả sửa đổi cục bộ, chưa tuyên bố phát hành.
- **Tier 3:** 7 test tập trung/546 test Python 3.10 đạt. Kiểm tra bản tải thật qua HTTP local, đọc lại cache offline, hash sai, tệp cắt ngắn và hai lượt Hugging Face song song. Audit phát hiện Content-Length hợp lệ vẫn có thể là tệp mô hình một byte; `dh-debug` thêm ngưỡng tối thiểu cho định dạng mô hình, rerun đạt. Không tải mô hình lớn từ mạng ngoài.
- **Tier 4:** không áp dụng.

Ngày: 2026-10-04. Mốc Git: `8cf344fe`; working tree có nhiều thay đổi chưa commit. Phạm vi: trạng thái DHSYSTEM, tài liệu, CLI, WebUI, tác vụ, TLS, runtime và gói Windows. Chưa chạy smoke media/GUI từ bản đóng gói.

## Cách kiểm chứng

- Python 3.10.19: `pytest -q -p no:cacheprovider` với `--basetemp` mới trong `%TEMP%` → **518 passed, 2 warnings**. Lần chạy đầu dùng `.pytest_cache/audit-tmp` bị 36 lỗi `PermissionError` do quyền thư mục cache hiện có; đây là lỗi môi trường chạy test, không phải 36 lỗi sản phẩm.
- `uv lock --check --offline` với cache uv sẵn có → **Resolved 422 packages**.
- Tái hiện độc lập: `BaseTask.set_end(succeed=True)` xóa thư mục thử nghiệm ngoài `config.TEMP_DIR`; `REQUESTS_CA_BUNDLE` tùy chỉnh bị thay bằng certifi; hai đầu vào CLI cùng tên cho cùng `target_dir`; `webui.build_ui()` báo giá trị ngôn ngữ không thuộc lựa chọn.
- Các kết luận về PyInstaller, Docker và hành vi khi chạy từ thư mục khác là phân tích tĩnh; chưa có log chạy artifact/container sạch.

## Tier 1 — nhất quán trạng thái: cảnh báo

| Mức | Phát hiện | Bằng chứng | Cần làm |
| --- | --- | --- | --- |
| Trung bình | Task 3.1 còn ghi manifest chỉ cho Python 3.10, trong khi manifest đã mở đến 3.12 trước khi GUI/media smoke hoàn tất. | `.DHSYSTEM/phases/3/tasks/3.1.md:29-34`, `pyproject.toml:4`, `docs/runtime-matrix.md:8` | Đồng bộ hợp đồng task và chỉ công bố runtime sau smoke. |
| Trung bình | Trạng thái audit, PLAN/SPEC, spec và version metadata đều chưa được Git theo dõi. Checkout sạch thiếu `sp.spec` và `version.txt`, nên workflow build hiện không chạy được. | `git ls-files sp.spec version.txt .DHSYSTEM/TRACKER.md docs/PLAN.md` trả rỗng | Lưu mốc Git trên nhánh có quyền trước CI. |
| Thấp | HANDOFF còn ngày 03/10 và task 3.1, không ghi phát hiện/nguy cơ mới của 04/10. | `.DHSYSTEM/HANDOFF.json:5-9`, `.DHSYSTEM/TRACKER.md` | Cập nhật khi chốt audit/đổi task. |

Phase 1–2 chỉ ghi `verified locally; git persistence pending`; không có tag `dh-p*-complete` là phù hợp với trạng thái hiện tại.

## Tier 2 — tài liệu: cảnh báo

| Mức | Phát hiện | Bằng chứng | Cần làm |
| --- | --- | --- | --- |
| Cao | Hướng dẫn WebUI/Docker còn nói mặc định `0.0.0.0`, chạy `--share` không cần credentials. Mã hiện mặc định `127.0.0.1` và bắt buộc credentials khi nghe mạng/share. Dockerfile đặt biến Gradio nhưng lệnh `python webui.py` dùng mặc định CLI loopback. | `docs/webui.md:28-56`, `Dockerfile:23-24,64`, `webui.py:1287-1295` | Sửa lệnh Docker và ví dụ triển khai, thêm biến xác thực. |
| Trung bình | Hướng dẫn dev nói `<3.11`; manifest là `<3.13`. README badge `3.10+` không nêu giới hạn trên. | `docs/dev-setup.md:3`, `pyproject.toml:4`, `README.md:16` | Đồng bộ theo ma trận runtime đã được kiểm chứng. |
| Thấp | Không có ma trận sơ đồ `ARCHITECTURE.md` để đối chiếu; `docs/architecture.md` là bản tường thuật. | `docs/architecture.md`, không có `ARCHITECTURE.md` gốc | Bổ sung nếu cần cổng tài liệu kiến trúc, sau lỗi phát hành. |

## Tier 3 — Python/PySide6/Gradio/PyInstaller: có lỗi và rủi ro cao

### Ưu tiên P0 — trước bản đóng gói dùng thật

1. **Cao — xóa dữ liệu ngoài cache quản lý khi kết thúc tác vụ.** `trans_create.py:25-33` chỉ kiểm đường cache khi `clear_cache=True`; `BaseTask.set_end()` luôn gọi `shutil.rmtree(self.cfg.cache_folder)` sau tác vụ thành công (`videotrans/task/_base.py:136-150`). Một cấu hình tác vụ đặt `cache_folder` ngoài `TEMP_DIR`, `clear_cache=False` sẽ bị xóa khi hoàn thành. Probe với thư mục riêng trong `%TEMP%` cho `outside_cache_exists_after_set_end=False`. Chặn xóa ở mọi điểm cleanup, kiểm tra symlink/đường đã resolve, chỉ xóa thư mục con do ứng dụng tạo.
2. **Cao — CLI có thể trộn/ghi đè kết quả của hai video cùng tên.** `cli.py:423-438` tạo `target_dir` từ basename, không gồm thư mục nguồn hay mã duy nhất; probe hai `clip.mp4` ở thư mục khác nhau cho cùng target nhưng cache khác. `trans_create.py:85-93` và `_stage_assemble.py:275` dùng tên SRT/WAV/MP4 cố định trong target đó. Cấp phát thư mục kết quả riêng hoặc có chính sách ghi đè rõ ràng; kiểm tra chạy song song và chạy lại.
3. **Cao — Docker WebUI mặc định không truy cập được qua cổng công bố.** `Dockerfile:23-24,62-64` chỉ đặt `GRADIO_SERVER_NAME=0.0.0.0`; `webui.py:1287-1295` dùng tham số `--host` mặc định `127.0.0.1`, và yêu cầu user/password cho chế độ mạng. Cần nối cấu hình Docker với CLI và cấp credentials; xác nhận bằng container smoke.
4. **Cao — ứng dụng đóng gói phụ thuộc CWD và thư mục exe phải ghi được.** `sp.py:74,141,246` đọc ảnh/QSS theo `./videotrans/...`; khởi chạy `sp.exe` từ CWD khác không tìm thấy QSS. `_paths.py:11,22-25` đặt models/logs/cache cạnh exe và tạo thư mục khi import, nên vị trí cài chỉ đọc làm app lỗi trước GUI. Dùng đường tài nguyên gắn với executable/package và thư mục dữ liệu người dùng; smoke từ CWD khác, đường có khoảng trắng và thư mục chỉ đọc.

### Ưu tiên P1 — sau khi bảo vệ dữ liệu và đường chạy chính

5. **Cao — đóng GUI có thể hủy tiến trình FFmpeg khác của cùng người dùng.** `videotrans/mainwin/_lifecycle.py:29-55,128` chạy `taskkill /F /FI "USERNAME eq ..." /IM ffmpeg.exe` hoặc `pkill -9 -u user ffmpeg`. Không giới hạn các PID do ứng dụng này tạo; đóng GUI có thể cắt tác vụ video độc lập. Quản lý subprocess handle/PID của chính ứng dụng.
6. **Cao — CA tùy chỉnh bị ghi đè.** `videotrans/configure/_paths.py:29-54,83` luôn đặt `CURL_CA_BUNDLE`, `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE` thành certifi, hoặc xóa các biến nếu lỗi. Probe đặt `REQUESTS_CA_BUNDLE` tới một tệp CA tồn tại, sao chép từ certifi, vẫn cho `valid_existing_custom_ca_preserved=False`. Máy dùng CA doanh nghiệp hoặc CA riêng mất cấu hình tin cậy; giữ giá trị hợp lệ do người dùng chỉ định, xử lý lỗi rõ ràng.
7. **Cao, cần xác nhận bằng artifact — PyInstaller có thể thiếu adapter và hộp thoại.** `sp.spec:75-100` liệt kê package cấp cao; `videotrans/__init__.py:27-29` và `videotrans/winform/__init__.py:29-55` dùng `importlib.import_module` với tên tạo lúc chạy. Không thấy `collect_submodules` hay danh sách đầy đủ module động. Phân tích bundle và mở ít nhất một kênh/đối thoại động trước khi phát hành.
8. **Trung bình — WebUI nạp giá trị ngôn ngữ không có trong dropdown.** `webui.py:156,1021-1028` dùng mã `en`, `zh-cn` từ params làm value, nhưng choices là tên hiển thị. Dựng `build_ui()` với cấu hình hiện có tạo cảnh báo Gradio cho cả hai ngôn ngữ. Chuyển code sang nhãn khi nạp, và nhãn sang code lúc submit.
9. **Trung bình — ma trận runtime và nguồn build chưa tái lập.** `pyproject.toml:4,275-277,333-334` công bố 3.10–3.12 nhưng `wetext` có wheel Windows `cp310`, Python 3.11 chưa test. Workflow tải FFmpeg từ URL `ffmpeg-git-full.7z` thay đổi (`.github/workflows/main.yml:60-68`); Chatterbox lấy nhánh `master` (`pyproject.toml:338`). Artifact SHA-256 chỉ ghi lại file đã build, không xác thực đầu vào. Ghim nguồn và hash, kiểm tra install/smoke theo runtime.
10. **Trung bình — `--lang en/zh` của desktop không chọn đúng ngôn ngữ.** `sp.py:134-137` nhận mã ngắn; `_i18n.py:46-53` chỉ nhận khóa locale như `en_US`, `zh_CN`, nên rơi về locale hệ điều hành. Thử với OS locale khác để xác nhận UI; chuẩn hóa mã khi parse.

### Độ tin cậy của kiểm thử

518 test xanh **không chứng minh** artifact hoạt động: workflow chỉ kiểm tệp tồn tại (`.github/workflows/main.yml:89-93`), chưa mở GUI/video. `tests/test_cli.py:490-513` có test mang tên `build_common_params` nhưng chỉ kiểm `callable`; `tests/test_ui_en_split.py:36-46` dùng `assert action.text() == title or action.text()` nên mọi nhãn không rỗng đều đạt; `tests/test_mainwin_actions.py:1-79` kiểm logic viết lại trong test. Không có test gọi `build_ui()` hay desktop `main()` với cấu hình lưu thực. Thêm các smoke/contract test ở đúng ranh giới người dùng, bỏ assertion không ràng buộc.

## Guardrails cho dh-auto

- P0: không xóa/move ngoài thư mục tác vụ đã kiểm chứng; chạy hai đầu vào cùng basename và xác nhận output độc lập.
- P0: mở bản gói từ CWD khác và nơi không ghi được; giải nén, chạy lại, kiểm output video/SRT/FFmpeg.
- P0: container nghe được qua `localhost:7860` của host với credentials bắt buộc, kiểm cả chế độ `--share`.
- P1: giữ CA do người dùng khai báo; chỉ dừng PID FFmpeg do ứng dụng tạo.
- P1: kiểm danh sách module trong artifact và chạy một adapter/hộp thoại động.
- P1: dùng nguồn phụ thuộc/binary cố định và checksum đầu vào; tách tuyên bố hỗ trợ core 3.12 với extra chỉ hỗ trợ 3.10.
- Không đánh dấu Phase 3 PASS khi mới có unit test hoặc kiểm layout; cần log build, GUI/media smoke và checksum artifact.

## Bổ sung sau vòng rà soát thứ hai (2026-10-04)

Các mục dưới đây **mới** so với phần trên; không thay đổi mức ưu tiên của các lỗi P0 đã ghi.

| Mức | Phát hiện và bằng chứng | Hướng xử lý |
| --- | --- | --- |
| Cao | **Cấu hình cũ làm ứng dụng không khởi động.** `videotrans/configure/_app_params.py:49-56` đọc thẳng `loaded['f5tts_role']` nhưng chỉ bắt `OSError` và `JSONDecodeError`. Probe tạo `params.json` hợp lệ `{}` rồi khởi tạo `AppParams` nhận `KeyError 'f5tts_role'`. Vì `config.py:25` tạo `AppParams()` khi import, lỗi xảy ra trước UI. | Dùng mặc định khi thiếu trường, kiểm kiểu và thêm test nâng cấp cấu hình cũ. |
| Cao, theo điều kiện | **Docker image có thể chứa khóa API cục bộ.** `Dockerfile:60` dùng `COPY . .`; `.dockerignore` không loại `videotrans/params.json`, `videotrans/cfg.json` hoặc `.env`. Hai tệp JSON cục bộ tồn tại trong workspace, còn `.gitignore:25-26` chỉ ngăn Git theo dõi. Nếu người dùng đã nhập khóa, build sẽ chép chúng vào layer image. | Loại cấu hình/secret khỏi build context; chỉ cấp qua volume hoặc biến môi trường khi chạy. Kiểm image không chứa file thử chứa secret. |
| Trung bình | **Hai lượt tải Hugging Face có thể thay đổi hàm tải toàn cục của nhau.** `videotrans/util/help_down.py:115,130,179-180` gán `hf_fd.http_get` trước khi lấy `download_lock` và khôi phục trong `finally`. Probe hai thread với `snapshot_download` giả cho `restored_while_b_active=True`: thread A đã khôi phục hàm gốc khi B còn đang ở trong lượt tải. Điều này có thể gán sai callback tiến độ hoặc mất theo dõi tải. | Không monkeypatch hàm toàn cục, hoặc khóa toàn bộ thời gian patch và restore; test hai lượt tải song song. |
| Trung bình | **Tệp model thiếu nội dung vẫn được xem là tải xong.** `videotrans/util/help_down.py:204-210` bỏ qua tải nếu file đích có kích thước >0, không kiểm hash, kích thước mong đợi hay cấu trúc. Probe đặt `weights.bin` một byte và URL không tồn tại: hàm trả `True` và giữ file một byte. | Xác minh checksum/size hoặc định dạng trước khi dùng cache; nếu không hợp lệ, tải lại vào file tạm và thay thế nguyên tử. |

Kiểm tra thêm: `ruff` với F821/F822/F823 không báo lỗi; `compileall` đạt khi chuyển pycache sang `%TEMP%`. Lần biên dịch đầu ghi vào `__pycache__` hiện có gặp `PermissionError`, là vấn đề quyền cache của môi trường audit.
