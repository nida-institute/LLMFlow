"""Ensure a usable CA bundle when running as a frozen (Nuitka) binary.

Nuitka onefile builds do not ship a usable system certificate store, so HTTPS
requests (urllib downloads, the `llm` package's API calls) fail with
CERTIFICATE_VERIFY_FAILED. Pointing the standard SSL env vars at the bundled
certifi CA bundle fixes this for urllib, requests, and httpx uniformly.

See LLMFlow#182.
"""
import os
import sys


def _is_frozen() -> bool:
    """True when running inside a Nuitka-compiled / frozen binary."""
    return bool(getattr(sys, "frozen", False)) or "__compiled__" in globals()


def ensure_ca_certs(frozen: bool | None = None) -> str | None:
    """Point SSL_CERT_FILE / REQUESTS_CA_BUNDLE at the bundled certifi CA bundle
    when running frozen.

    No-op when not frozen, and never overrides a value the user has already set
    (``setdefault``). Returns the CA path when applied, else ``None``.
    """
    if frozen is None:
        frozen = _is_frozen()
    if not frozen:
        return None
    try:
        import certifi
    except Exception:
        return None
    ca = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", ca)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", ca)
    return ca
