"""Tests for CA-bundle setup used by the frozen binary (LLMFlow#182).

The Nuitka onefile binary ships no usable system cert store, so HTTPS fails with
CERTIFICATE_VERIFY_FAILED. `ensure_ca_certs()` points the standard SSL env vars at
the bundled certifi CA bundle when frozen.
"""
import os

import certifi

from llmflow.utils.ssl_certs import ensure_ca_certs


def test_sets_ca_env_when_frozen(monkeypatch):
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    result = ensure_ca_certs(frozen=True)
    assert result == certifi.where()
    assert os.environ["SSL_CERT_FILE"] == certifi.where()
    assert os.environ["REQUESTS_CA_BUNDLE"] == certifi.where()


def test_noop_when_not_frozen(monkeypatch):
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    assert ensure_ca_certs(frozen=False) is None
    assert "SSL_CERT_FILE" not in os.environ


def test_does_not_override_user_value(monkeypatch):
    monkeypatch.setenv("SSL_CERT_FILE", "/custom/ca.pem")
    ensure_ca_certs(frozen=True)
    assert os.environ["SSL_CERT_FILE"] == "/custom/ca.pem"
