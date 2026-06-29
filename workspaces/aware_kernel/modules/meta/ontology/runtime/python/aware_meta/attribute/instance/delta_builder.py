from __future__ import annotations

from typing import Any, Literal

import difflib


DeltaKind = Literal["text_patch", "scalar_set"]


def compute_text_patches(old_text: str, new_text: str) -> list[dict[str, Any]]:
    """
    Compute text patches using difflib.SequenceMatcher.

    This is a direct, library-local port of the logic previously implemented
    on ContentPartText; it lives here so attribute / primitive change builders
    can own text deltas without depending on content-part models.
    """
    if old_text == new_text:
        return []

    patches: list[dict[str, Any]] = []
    matcher = difflib.SequenceMatcher(None, old_text, new_text)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            if i2 > i1 and j2 > j1:
                patches.append(
                    {
                        "op": "replace",
                        "pos": i1,
                        "len": i2 - i1,
                        "text": new_text[j1:j2],
                    }
                )
            elif i2 > i1:
                patches.append({"op": "delete", "pos": i1, "len": i2 - i1})
            elif j2 > j1:
                patches.append({"op": "insert", "pos": i1, "text": new_text[j1:j2]})
        elif tag == "delete":
            patches.append({"op": "delete", "pos": i1, "len": i2 - i1})
        elif tag == "insert":
            patches.append({"op": "insert", "pos": i1, "text": new_text[j1:j2]})

    return consolidate_patches(patches)


def consolidate_patches(patches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Consolidate adjacent patches to minimize the number of operations.
    """
    if not patches:
        return patches

    consolidated: list[dict[str, Any]] = []
    i = 0
    while i < len(patches):
        current_patch = patches[i].copy()

        if current_patch["op"] == "insert":
            j = i + 1
            while j < len(patches):
                next_patch = patches[j]
                if next_patch["op"] == "insert" and next_patch["pos"] == current_patch["pos"]:
                    current_patch["text"] += next_patch["text"]
                    j += 1
                else:
                    break
            i = j

        elif current_patch["op"] == "delete":
            j = i + 1
            while j < len(patches):
                next_patch = patches[j]
                if next_patch["op"] == "delete" and next_patch["pos"] == current_patch["pos"]:
                    current_patch["len"] += next_patch["len"]
                    j += 1
                else:
                    break
            i = j

        elif current_patch["op"] == "replace":
            j = i + 1
            while j < len(patches):
                next_patch = patches[j]
                if next_patch["op"] == "replace" and next_patch["pos"] == current_patch["pos"] + current_patch["len"]:
                    current_patch["len"] += next_patch["len"]
                    current_patch["text"] += next_patch["text"]
                    j += 1
                else:
                    break
            i = j
        else:
            i += 1

        consolidated.append(current_patch)

    return consolidated


def build_primitive_delta(
    old_value: Any,
    new_value: Any,
    base_type: str | None = None,
) -> tuple[DeltaKind, dict[str, Any] | None]:
    """
    Build a delta descriptor for primitive scalar changes.

    - For string-like primitives, returns a \"text_patch\" delta with consolidated patches.
    - For all other scalar types, returns a \"scalar_set\" delta with the new value.
    """
    is_text = base_type == "string" or (isinstance(old_value, str) and isinstance(new_value, str))

    if is_text:
        patches = compute_text_patches(old_value, new_value)
        # Even if patches end up empty (defensive), fall back to scalar_set.
        if patches:
            return "text_patch", {"patches": patches}
        return "scalar_set", {"value": new_value}

    # Default: simple scalar set
    return "scalar_set", {"value": new_value}


__all__ = [
    "DeltaKind",
    "compute_text_patches",
    "consolidate_patches",
    "build_primitive_delta",
]
