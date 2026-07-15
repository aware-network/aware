from __future__ import annotations

import os
from urllib.parse import urlparse

_NODE_BASE_URL_ENV = "AWARE_NODE_BASE_URL"
_NODE_ENVIRONMENT_BASE_URL_ENV = "AWARE_NODE_ENVIRONMENT_BASE_URL"
_LOCAL_ENVIRONMENT_BASE_URL = "http://127.0.0.1"
_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "0.0.0.0"}


def resolve_node_environment_publication_endpoint(
    *,
    environment_port: int | None,
    configured_base_url: str | None,
    configured_full_url: str | None,
) -> str | None:
    explicit_base_url = _clean_url(os.environ.get(_NODE_ENVIRONMENT_BASE_URL_ENV))
    if environment_port is None:
        return explicit_base_url or _clean_url(configured_full_url)
    if explicit_base_url is not None:
        return _with_port(explicit_base_url, environment_port)
    if _node_publication_is_local():
        return _with_port(_LOCAL_ENVIRONMENT_BASE_URL, environment_port)

    configured_base = _clean_url(configured_base_url)
    if configured_base is not None:
        return _with_port(configured_base, environment_port)
    return _clean_url(configured_full_url)


def _node_publication_is_local() -> bool:
    node_base_url = _clean_url(os.environ.get(_NODE_BASE_URL_ENV))
    if node_base_url is None:
        return True
    parsed = urlparse(node_base_url)
    host = parsed.hostname
    return host is None or host.lower() in _LOCAL_HOSTS


def _clean_url(value: str | None) -> str | None:
    cleaned = (value or "").strip().rstrip("/")
    return cleaned or None


def _with_port(base_url: str, port: int) -> str:
    parsed = urlparse(base_url)
    if parsed.port is not None:
        return base_url
    return f"{base_url}:{port}"
