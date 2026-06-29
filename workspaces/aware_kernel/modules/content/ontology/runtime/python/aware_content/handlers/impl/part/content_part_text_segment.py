from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Content Ontology
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_style import ContentPartTextStyle
from aware_orm.session.change_collector import current_change_collector

# --- AWARE: USER_IMPORTS END


async def upsert(
    segment_id: UUID | None = None,
    content_part_text_id: UUID | None = None,
    byte_start: int | None = None,
    byte_end: int | None = None,
    style_id: UUID | None = None,
    parent_id: UUID | None = None,
) -> ContentPartTextSegment:
    """
    Creates a text segment with a deterministic id.

    Contract:
    - `content_part_text_id` is required for new segments.
    - `byte_start`/`byte_end` are UTF-8 byte offsets into the target text's `inline_text`.
    - `style_id` references a `ContentPartTextStyle` (caller may create-or-get styles separately).
    """

    # --- AWARE: LOGIC START upsert
    existing = ContentPartTextSegment.get_by_id_sync(segment_id)
    if existing is not None:
        raise ValueError(
            "ContentPartTextSegment.upsert is create-only (v1); "
            "use ContentPartTextSegment.update_segment(...) or delete_segment(...)."
        )

    if content_part_text_id is None:
        raise ValueError(
            "ContentPartTextSegment.upsert cannot create a detached segment; "
            "content_part_text_id is required for new segments."
        )

    content_part_text = ContentPartText.get_by_id_sync(content_part_text_id)
    if content_part_text is None:
        raise ValueError(
            "ContentPartText must be present in the identity map to create segments: "
            f"content_part_text_id={content_part_text_id}"
        )

    style = (
        ContentPartTextStyle.get_by_id_sync(style_id) if style_id is not None else None
    )

    return ContentPartTextSegment(
        id=segment_id,
        content_part_text_id=content_part_text_id,
        content_part_text=content_part_text,
        byte_start=byte_start,
        byte_end=byte_end,
        style_id=style_id,
        style=style,
        parent_id=parent_id,
    )
    # --- AWARE: LOGIC END upsert


async def update_segment(
    content_part_text_segment: ContentPartTextSegment,
    content_part_text_id: UUID,
    byte_start: int | None = None,
    byte_end: int | None = None,
    style_id: UUID | None = None,
    parent_id: UUID | None = None,
) -> None:
    """
    Updates an existing segment (v1).

    Contract:
    - `content_part_text_id` remains required.
    - `byte_start`/`byte_end` are UTF-8 byte offsets into the attached text's `inline_text`.
    """

    # --- AWARE: LOGIC START update_segment
    content_part_text_segment.byte_start = byte_start
    content_part_text_segment.byte_end = byte_end
    content_part_text_segment.parent_id = parent_id
    content_part_text_segment.content_part_text_id = content_part_text_id
    content_part_text_segment.style = (
        ContentPartTextStyle.get_by_id_sync(style_id) if style_id is not None else None
    )

    content_part_text = ContentPartText.get_by_id_sync(content_part_text_id)
    if content_part_text is not None:
        content_part_text_segment.content_part_text = content_part_text
    # --- AWARE: LOGIC END update_segment


async def delete_segment(content_part_text_segment: ContentPartTextSegment) -> None:
    """
    Deletes this segment explicitly from the lane.
    """

    # --- AWARE: LOGIC START delete_segment
    style = getattr(content_part_text_segment, "style", None)
    style_id = getattr(content_part_text_segment, "style_id", None)
    if style is None and style_id is not None:
        style = ContentPartTextStyle.get_by_id_sync(style_id)

    collector = current_change_collector()
    if collector is not None:
        collector.record_delete(content_part_text_segment)

    content_part_text = getattr(content_part_text_segment, "content_part_text", None)
    if content_part_text is not None and getattr(content_part_text, "segments", None):
        content_part_text.segments[:] = [
            segment
            for segment in content_part_text.segments
            if getattr(segment, "id", None) != content_part_text_segment.id
        ]

    bound_session = content_part_text_segment.bound_session
    if bound_session is not None:
        bound_session.imap_remove(
            type(content_part_text_segment), content_part_text_segment.id
        )

    if style is not None:
        await style.delete_if_unreferenced()
    # --- AWARE: LOGIC END delete_segment
