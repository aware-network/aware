from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Content Ontology
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_editor_patch import ContentPartTextEditorPatch

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from uuid import uuid4

from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_content_ontology.part.content_part_text_style import ContentPartTextStyle

from aware_content.part.text.apply import apply_text_patches

# --- AWARE: USER_IMPORTS END


async def create_content_part_text(
    key: str = "default", inline_text: str | None = None
) -> ContentPartText:
    """
    Creates a new text content part container.
    """

    # --- AWARE: LOGIC START create_content_part_text
    return ContentPartText(id=uuid4(), key=key, inline_text=inline_text)
    # --- AWARE: LOGIC END create_content_part_text


async def set_inline_text(content_part_text: ContentPartText, inline_text: str) -> None:
    """
    Updates the inline_text for this ContentPartText (v0 editor persistence).
    """

    # --- AWARE: LOGIC START set_inline_text
    content_part_text.inline_text = inline_text
    # --- AWARE: LOGIC END set_inline_text


async def apply_editor_patch(
    content_part_text: ContentPartText, patch: ContentPartTextEditorPatch
) -> None:
    """
    Applies a canonical editor patch (v1).

    Contract:
    - `patch.text_after` or `patch.text_patches` update `inline_text`.
    - `patch.segment_ops` upserts/deletes `ContentPartTextSegment` objects.
    - Segment `byte_*` ranges are UTF-8 byte offsets into `inline_text`.
    """

    # --- AWARE: LOGIC START apply_editor_patch
    current_text = content_part_text.inline_text or ""
    next_text = current_text

    text_after = patch.text_after
    text_patches = list(patch.text_patches)
    if text_after is not None:
        next_text = str(text_after)
    elif text_patches:
        next_text = apply_text_patches(current_text, text_patches)

    if next_text != current_text:
        content_part_text.inline_text = next_text

    text_bytes_len = len(next_text.encode("utf-8"))
    segment_ops = list(patch.segment_ops)

    for op in segment_ops:
        upsert = op.upsert
        detach = op.detach

        if upsert is not None:
            segment_id = upsert.segment_id
            start = int(upsert.byte_start)
            end = int(upsert.byte_end)
            parent_id = upsert.parent_id

            if start < 0 or end < start or end > text_bytes_len:
                raise ValueError(
                    "Invalid segment byte range: "
                    f"segment_id={segment_id} byte_start={start} byte_end={end} text_bytes_len={text_bytes_len}"
                )

            style_spec = upsert.style
            style_id = None
            if style_spec is not None:
                style = await ContentPartTextStyle.create_or_get_style_via_content_part_text_segment(
                    content_part_text_segment_id=segment_id,
                    font_family=style_spec.font_family,
                    font_size=style_spec.font_size,
                    bold=style_spec.bold,
                    italic=style_spec.italic,
                    underline=style_spec.underline,
                    color=style_spec.color,
                    background_color=style_spec.background_color,
                    block_semantic_type=style_spec.block_semantic_type,
                )
                style_id = style.id

            existing_segment = ContentPartTextSegment.get_by_id_sync(segment_id)
            if existing_segment is None:
                created = await ContentPartTextSegment.upsert_via_content_part_text(
                    segment_id=segment_id,
                    content_part_text_id=content_part_text.id,
                    byte_start=start,
                    byte_end=end,
                    style_id=style_id,
                    parent_id=parent_id,
                )
                segment_ids = {
                    getattr(s, "id", None) for s in content_part_text.segments
                }
                if created.id not in segment_ids:
                    content_part_text.segments.append(created)
            else:
                await existing_segment.update_segment(
                    content_part_text_id=content_part_text.id,
                    byte_start=start,
                    byte_end=end,
                    style_id=style_id,
                    parent_id=parent_id,
                )
                segment_ids = {
                    getattr(s, "id", None) for s in content_part_text.segments
                }
                if existing_segment.id not in segment_ids:
                    content_part_text.segments.append(existing_segment)
            continue

        if detach is not None:
            segment_id = detach.segment_id
            existing_segment = ContentPartTextSegment.get_by_id_sync(segment_id)
            if existing_segment is None:
                raise ValueError(
                    "Cannot detach unknown segment (not in identity map): "
                    f"segment_id={segment_id}"
                )
            await existing_segment.delete_segment()
            if content_part_text.segments:
                content_part_text.segments[:] = [
                    seg
                    for seg in content_part_text.segments
                    if getattr(seg, "id", None) != segment_id
                ]
            continue

        raise ValueError(
            "Invalid ContentPartTextSegmentOp: expected `upsert` or `detach`"
        )
    # --- AWARE: LOGIC END apply_editor_patch


async def delete(content_part_text: ContentPartText) -> None:
    """
    Deletes this text content part and all owned segments.
    """

    # --- AWARE: LOGIC START delete
    for segment in list(content_part_text.segments):
        await segment.delete_segment()
    if content_part_text.segments:
        content_part_text.segments[:] = []

    from aware_orm.session.change_collector import current_change_collector

    collector = current_change_collector()
    if collector is None:
        raise RuntimeError(
            "ContentPartText.delete requires an active runtime change collector"
        )

    collector.record_delete(content_part_text)
    if content_part_text.bound_session is not None:
        content_part_text.bound_session.imap_remove(
            type(content_part_text), content_part_text.id
        )
    # --- AWARE: LOGIC END delete


async def get_next_segment_position(
    content_part_text: ContentPartText, content_part_text_id: UUID
) -> int:
    """
    Gets the next available position for a text segment within a content part text.
    Parameters: p_content_part_text_id: The UUID of the content part text.
    """

    # --- AWARE: LOGIC START get_next_segment_position
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END get_next_segment_position


async def increment_segment_positions(
    content_part_text: ContentPartText,
    p_content_part_text_id: UUID,
    p_start_position: int,
) -> None:
    """
    Increments the positions of text segments within a content part text.
    Parameters: p_content_part_text_id: The UUID of the content part text.
    p_start_position: The position to start incrementing from.
    """

    # --- AWARE: LOGIC START increment_segment_positions
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END increment_segment_positions


async def merge_segments(
    content_part_text: ContentPartText,
    p_content_part_text_id: UUID,
    p_first_position: int,
    p_second_position: int,
) -> UUID:
    """
    Merges two text segments within a content part text.
    Parameters: p_content_part_text_id: The UUID of the content part text.
    p_first_position: The position of the first segment to merge.
    p_second_position: The position of the second segment to merge.
    """

    # --- AWARE: LOGIC START merge_segments
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END merge_segments
