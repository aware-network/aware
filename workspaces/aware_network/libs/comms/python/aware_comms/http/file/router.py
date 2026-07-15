from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from aware_comms.http import utils as http_utils
from aware_comms.http.file.model import DownloadFileRequest, UploadFileResponse

logger = logging.getLogger(__name__)


class FileRouter(BaseModel):
    """Specialized router for file upload/download operations."""

    upload_handler: Callable[[UploadFile, UUID], Awaitable[UploadFileResponse]]
    download_handler: Callable[[DownloadFileRequest, UUID], Awaitable[FileResponse]]

    def register(self) -> APIRouter:
        router = APIRouter()

        @router.post("/crud/upload")
        async def upload_file(  # pyright: ignore[reportUnusedFunction]
            file: Annotated[UploadFile, File()],
            user_id: Annotated[UUID, Depends(http_utils.get_current_user_id)],
        ):
            try:
                return await self.upload_handler(file, user_id)
            except Exception as exc:  # noqa: PERF203
                logger.error("Error handling file upload: %s", str(exc))
                raise

        @router.get("/crud/download")
        async def download_file(  # pyright: ignore[reportUnusedFunction]
            request: Annotated[DownloadFileRequest, Depends(DownloadFileRequest)],
            user_id: Annotated[UUID, Depends(http_utils.get_current_user_id)],
        ):
            try:
                return await self.download_handler(request, user_id)
            except Exception as exc:  # noqa: PERF203
                logger.error("Error handling file download: %s", str(exc))
                raise

        return router


__all__ = ["FileRouter"]
