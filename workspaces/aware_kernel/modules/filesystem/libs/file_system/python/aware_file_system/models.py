import os
import mimetypes
import hashlib
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class FileType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    OTHER = "other"


class FileMetadata(BaseModel):
    """
    Pydantic model representing metadata for a single file, with additional tracking features.
    """

    path: str = Field(..., description="Relative path of the file within the project")
    name: str = Field(..., description="Name of the file")
    size: int = Field(..., description="Size of the file in bytes")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    file_type: FileType = Field(..., description="Type of the file")
    mime_type: str = Field(..., description="MIME type of the file")
    depth: int = Field(..., description="Depth of the file in the directory structure")
    hash: str = Field(..., description="Hash of the file content")
    content: bytes = Field(..., description="File content as bytes")

    @classmethod
    def from_file(cls, file_path: str, root_path: str) -> "FileMetadata":
        stat = os.stat(file_path)
        relative_path = os.path.relpath(file_path, root_path)
        depth = relative_path.count(os.sep)
        mime_type, _ = mimetypes.guess_type(file_path)

        with open(file_path, "rb") as f:
            content = f.read()

        file_hash = hashlib.md5(content).hexdigest()

        return cls(
            path=relative_path,
            name=os.path.basename(file_path),
            size=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            file_type=cls._get_file_type(mime_type),
            mime_type=mime_type or "application/octet-stream",
            depth=depth,
            hash=file_hash,
            content=content,
        )

    def is_modified(self, other: "FileMetadata") -> bool:
        """
        Check if this file is modified compared to another FileMetadata instance.

        Args:
            other (FileMetadata): The FileMetadata to compare against.

        Returns:
            bool: True if the file is modified, False otherwise.
        """
        if self.size != other.size or self.last_modified != other.last_modified:
            return True
        if self.hash and other.hash:
            return self.hash != other.hash
        return False

    @staticmethod
    def _get_file_type(mime_type: Optional[str]) -> FileType:
        """
        Determine the FileType based on the MIME type.

        Args:
            mime_type (Optional[str]): The MIME type of the file.

        Returns:
            FileType: The determined FileType enum value.
        """
        if mime_type:
            if mime_type.startswith("text"):
                return FileType.TEXT
            elif mime_type.startswith("audio"):
                return FileType.AUDIO
            elif mime_type.startswith("image"):
                return FileType.IMAGE
            elif mime_type.startswith("video"):
                return FileType.VIDEO
        return FileType.OTHER

    @staticmethod
    def _get_mime_type(file_path: str) -> str:
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"


class ChangeType(str, Enum):
    create = "create"
    delete = "delete"
    update = "update"


class Changes(BaseModel):
    """
    Pydantic model representing changes in the project structure.
    """

    changes: dict[ChangeType, list[str]] = Field(
        default_factory=lambda: {ct: [] for ct in ChangeType},
        description="Dictionary of change types to lists of file paths",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of when changes were detected",
    )


FilePathMetadata = dict[str, FileMetadata]


class ProjectStructure(BaseModel):
    """
    Pydantic model representing the overall structure of the project.
    """

    root_path: str = Field(..., description="Absolute path to the project root")
    tree: str = Field(..., description="String representation of the project tree")
    files_metadata: FilePathMetadata = Field(default_factory=dict, description="Dictionary of file paths to metadata")
    total_size: int = Field(0, description="Total size of all included files in bytes")
    file_count: int = Field(0, description="Total number of included files")
    max_depth: int = Field(0, description="Maximum depth of the directory structure")
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of the last analysis",
    )

    def get_abs_file_paths(self) -> list[str]:
        return [os.path.join(self.root_path, file_path) for file_path in self.files_metadata.keys()]


class Diff(BaseModel):
    file_path: str
    file_type: FileType
    change_type: ChangeType
    diff_content: str
    new_content: Optional[bytes] = None


class Report(BaseModel):
    summary: dict[ChangeType, dict[FileType, int]]
    diffs: list[Diff]


class ProjectUpdate(BaseModel):
    project_structure: ProjectStructure
    changes: Optional[Changes]
    report: Report
