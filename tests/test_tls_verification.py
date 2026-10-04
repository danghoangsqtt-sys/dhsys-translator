import ast
import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from videotrans.configure.config import params
from videotrans.translator._transapi import TransAPI
from videotrans.configure._paths import fix_ssl_cert_env


def test_product_clients_never_disable_certificate_verification():
    root = Path(__file__).resolve().parents[1] / "videotrans"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if keyword.arg in ("verify", "ssl_verify"):
                    assert not isinstance(keyword.value, ast.Constant) or keyword.value.value is not False, path


def test_custom_translation_api_uses_requests_default_tls(monkeypatch):
    monkeypatch.setitem(params, "trans_api_url", "https://example.com/translate")
    response = Mock()
    response.json.return_value = {"code": 0, "text": "xin chào"}
    request = Mock(return_value=response)
    monkeypatch.setattr("videotrans.translator._transapi.requests.get", request)

    api = TransAPI(source_code="en", target_code="vi")
    assert api._item_task("hello") == "xin chào"
    assert request.call_args.kwargs.get("verify", True) is True


def test_custom_ca_bundle_is_preserved(monkeypatch, tmp_path):
    bundle = tmp_path / "enterprise-ca.pem"
    bundle.write_text("test certificate", encoding="utf-8")
    for key in ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "SSL_CERT_FILE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(bundle))

    fix_ssl_cert_env()

    assert all(os.environ[key] == str(bundle) for key in
               ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "SSL_CERT_FILE"))


def test_missing_explicit_ca_bundle_has_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(tmp_path / "missing.pem"))

    with pytest.raises(FileNotFoundError, match="REQUESTS_CA_BUNDLE"):
        fix_ssl_cert_env()


def test_ca_bundle_uses_certifi_when_not_configured(monkeypatch):
    import certifi
    for key in ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "SSL_CERT_FILE"):
        monkeypatch.delenv(key, raising=False)

    fix_ssl_cert_env()

    assert all(os.environ[key] == certifi.where() for key in
               ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "SSL_CERT_FILE"))
