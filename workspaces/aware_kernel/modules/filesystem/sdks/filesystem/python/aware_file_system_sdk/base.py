from __future__ import annotations

from pathlib import Path


class FileSystemSdkError(RuntimeError):
    pass


def normalize_relative_path(value: str) -> str:
    raw = value.strip()
    if Path(raw).is_absolute():
        raise FileSystemSdkError("FileSystem SDK path must be root-relative.")
    parts: list[str] = []
    for part in Path(raw).as_posix().strip("/").split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            raise FileSystemSdkError(
                "FileSystem SDK path escapes the filesystem root."
            )
        parts.append(part)
    return "/".join(parts) if parts else "."


__all__ = [
    "FileSystemSdkError",
    "normalize_relative_path",
]
