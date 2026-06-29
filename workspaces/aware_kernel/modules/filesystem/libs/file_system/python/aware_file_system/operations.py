"""Filesystem operations mediated for AWARE handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional


@dataclass(frozen=True)
class FileOpReceipt:
    operation: str
    path: Path
    existed: bool
    bytes_written: int | None = None
    authorised_paths: Mapping[str, tuple[str, ...]] | None = field(default=None)


def ensure_directory(path: Path, *, exist_ok: bool = True) -> FileOpReceipt:
    existed = path.exists()
    if not existed:
        path.mkdir(parents=True, exist_ok=exist_ok)
    return FileOpReceipt(operation="ensure_directory", path=path, existed=existed)


def write_file(path: Path, content: str, *, overwrite: bool = False) -> FileOpReceipt:
    existed = path.exists()
    if existed and not overwrite:
        raise FileExistsError(f"{path} already exists; use overwrite=True to replace.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return FileOpReceipt(operation="write_file", path=path, existed=existed, bytes_written=len(content))


def append_file(path: Path, content: str) -> FileOpReceipt:
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    mode = "a" if existed else "w"
    with path.open(mode, encoding="utf-8") as fh:
        fh.write(content)
    return FileOpReceipt(operation="append_file", path=path, existed=existed, bytes_written=len(content))


def move_path(src: Path, dst: Path, *, overwrite: bool = False) -> FileOpReceipt:
    if not src.exists():
        raise FileNotFoundError(f"Source path '{src}' does not exist.")
    if dst.exists():
        if not overwrite:
            raise FileExistsError(f"Destination path '{dst}' already exists.")
        if dst.is_dir():
            for child in dst.iterdir():
                if child.is_dir():
                    _remove_tree(child)
                else:
                    child.unlink()
        else:
            dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return FileOpReceipt(operation="move_path", path=dst, existed=False)


def delete_path(path: Path) -> FileOpReceipt:
    if not path.exists():
        return FileOpReceipt(operation="delete_path", path=path, existed=False)
    if path.is_dir():
        _remove_tree(path)
    else:
        path.unlink()
    return FileOpReceipt(operation="delete_path", path=path, existed=True)


def _remove_tree(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            _remove_tree(child)
        else:
            child.unlink()
    path.rmdir()
