from __future__ import annotations

# Compatibility mount for the Node HTTP server. Storage owns the data-plane
# implementation; Node should not be the raw media authority.
from aware_storage_service.http_file_ops import (
    download_file_handler,
    upload_file_handler,
)


__all__ = ["download_file_handler", "upload_file_handler"]
