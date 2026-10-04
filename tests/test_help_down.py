import hashlib
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import huggingface_hub
import huggingface_hub.file_download as hf_fd
import pytest
import requests
from huggingface_hub.errors import LocalEntryNotFoundError

from videotrans.configure.excepts import DownloadModelsError
from videotrans.util import help_down

MODEL_BYTES = b"model" * 300


class FakeResponse:
    def __init__(self, content=MODEL_BYTES, declared_size=None, status_code=200, headers=None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {"content-length": str(declared_size or len(content))}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def iter_content(self, chunk_size):
        yield self.content

    def raise_for_status(self):
        raise AssertionError("unexpected HTTP status")


class FakeSession:
    def __init__(self, content=MODEL_BYTES, declared_size=None):
        self.content = content
        self.declared_size = declared_size or len(content)
        self.get_calls = 0
        self.head_calls = 0

    def head(self, *_args, **_kwargs):
        self.head_calls += 1
        return FakeResponse(self.content, self.declared_size)

    def get(self, *_args, **_kwargs):
        self.get_calls += 1
        return FakeResponse(self.content, self.declared_size)


def test_one_byte_cached_model_is_replaced_atomically(tmp_path, monkeypatch):
    cached = tmp_path / "weights.bin"
    cached.write_bytes(b"x")
    session = FakeSession()
    monkeypatch.setattr(requests, "Session", lambda: session)
    monkeypatch.setattr(help_down, "max_retries", 1)

    assert help_down.down_file_from_hf(tmp_path, ["https://example.com/weights.bin"])

    assert cached.read_bytes() == MODEL_BYTES
    assert (tmp_path / "weights.bin.sha256").read_text(encoding="ascii").strip() == hashlib.sha256(MODEL_BYTES).hexdigest()
    assert session.head_calls == 0
    assert session.get_calls == 1


def test_verified_cached_model_skips_network(tmp_path, monkeypatch):
    cached = tmp_path / "weights.bin"
    cached.write_bytes(MODEL_BYTES)
    (tmp_path / "weights.bin.sha256").write_text(hashlib.sha256(MODEL_BYTES).hexdigest(), encoding="ascii")
    session = FakeSession()
    monkeypatch.setattr(requests, "Session", lambda: session)

    assert help_down.down_file_from_hf(tmp_path, ["https://example.com/weights.bin"])
    assert session.head_calls == 0
    assert session.get_calls == 0


def test_truncated_download_never_replaces_old_file(tmp_path, monkeypatch):
    old = tmp_path / "weights.bin"
    old.write_bytes(b"oldfile")
    session = FakeSession(content=b"xx", declared_size=2000)
    monkeypatch.setattr(requests, "Session", lambda: session)
    monkeypatch.setattr(help_down, "max_retries", 1)

    with pytest.raises(DownloadModelsError):
        help_down.down_file_from_hf(tmp_path, ["https://example.com/weights.bin"])

    assert old.read_bytes() == b"oldfile"


def test_server_claiming_one_byte_model_is_rejected(tmp_path, monkeypatch):
    cached = tmp_path / "weights.bin"
    cached.write_bytes(b"x")
    session = FakeSession(content=b"x", declared_size=1)
    monkeypatch.setattr(requests, "Session", lambda: session)
    monkeypatch.setattr(help_down, "max_retries", 1)

    with pytest.raises(DownloadModelsError):
        help_down.down_file_from_hf(tmp_path, ["https://example.com/weights.bin"])

    assert session.get_calls == 1
    assert cached.read_bytes() == b"x"


def test_hash_in_url_rejects_wrong_download(tmp_path, monkeypatch):
    expected = hashlib.sha256(b"correct" * 300).hexdigest()
    session = FakeSession(content=b"wrong" * 300)
    monkeypatch.setattr(requests, "Session", lambda: session)
    monkeypatch.setattr(help_down, "max_retries", 1)

    with pytest.raises(DownloadModelsError):
        help_down.down_file_from_hf(tmp_path, [f"https://example.com/{expected}/weights.bin"])

    assert not (tmp_path / "weights.bin").exists()


def test_parallel_hf_snapshots_do_not_patch_global_http_get(tmp_path, monkeypatch):
    monkeypatch.setattr("videotrans.util.help_misc.is_connect_hf", lambda: True)
    original_http_get = hf_fd.http_get
    events = {"a": [], "b": []}

    def fake_snapshot_download(**kwargs):
        if kwargs.get("local_files_only"):
            raise LocalEntryNotFoundError("missing")
        assert hf_fd.http_get is original_http_get
        progress = kwargs["tqdm_class"](total=2, disable=True)
        progress.update(1)
        progress.close()
        return kwargs["local_dir"]

    monkeypatch.setattr(huggingface_hub, "snapshot_download", fake_snapshot_download)

    def run(name):
        return help_down.check_and_down_hf(name, f"example/{name}", tmp_path / name,
                                           callback=events[name].append)

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(run, ("a", "b"))) == [True, True]

    assert hf_fd.http_get is original_http_get
    assert all(any(isinstance(event, dict) and event.get("type") == "batch"
                   for event in events[name]) for name in ("a", "b"))


def test_small_real_http_download_and_offline_cache_reuse(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "weights.bin").write_bytes(MODEL_BYTES)
    output = tmp_path / "output"
    handler = partial(SimpleHTTPRequestHandler, directory=str(source))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/weights.bin"
    try:
        assert help_down.down_file_from_hf(output, [url])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert (output / "weights.bin").read_bytes() == MODEL_BYTES
    assert help_down.down_file_from_hf(output, [url])
