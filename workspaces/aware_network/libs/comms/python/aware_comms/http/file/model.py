from uuid import UUID

from pydantic import BaseModel


class DownloadFileRequest(BaseModel):
    object_id: UUID


class UploadFileResponse(BaseModel):
    object_id: UUID
    sha: str
    mime_type: str
    size_bytes: int


__all__ = ["DownloadFileRequest", "UploadFileResponse"]
