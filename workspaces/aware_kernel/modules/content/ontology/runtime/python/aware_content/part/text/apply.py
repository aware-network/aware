from __future__ import annotations

from typing import Iterable

from aware_content_ontology.part.content_part_text_editor_patch import (
    ContentTextPatch,
    ContentTextPatchOp,
)


def apply_text_patches(current_text: str, patches: Iterable[ContentTextPatch]) -> str:
    """
    Apply a sequence of text patches to the current text.
    """
    data = bytearray(current_text.encode("utf-8"))
    for patch in patches:
        pos = int(patch.pos)
        if pos < 0 or pos > len(data):
            raise ValueError(f"ContentTextPatch.pos out of range: pos={pos} len={len(data)}")
        op = patch.op
        if op == ContentTextPatchOp.insert:
            text = patch.text or ""
            data[pos:pos] = text.encode("utf-8")
            continue
        if op == ContentTextPatchOp.delete:
            length = patch.len
            if length is None:
                raise ValueError("ContentTextPatch.delete requires len")
            length = int(length)
            if length < 0 or (pos + length) > len(data):
                raise ValueError(f"ContentTextPatch.delete out of range: pos={pos} len={length} data_len={len(data)}")
            del data[pos : pos + length]
            continue
        if op == ContentTextPatchOp.replace:
            length = patch.len
            if length is None:
                raise ValueError("ContentTextPatch.replace requires len")
            length = int(length)
            if length < 0 or (pos + length) > len(data):
                raise ValueError(f"ContentTextPatch.replace out of range: pos={pos} len={length} data_len={len(data)}")
            text = patch.text or ""
            data[pos : pos + length] = text.encode("utf-8")
            continue
        raise ValueError(f"Unsupported ContentTextPatchOp: {op!r}")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "ContentTextPatch produced invalid UTF-8 bytes; " "patch offsets must align to UTF-8 boundaries."
        ) from exc
