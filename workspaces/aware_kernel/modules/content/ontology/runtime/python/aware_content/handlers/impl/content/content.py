from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Content Ontology
from aware_content_ontology.content.content_enums import ContentSource
from aware_content_ontology.content.content import Content

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_content_ontology.part.content_part import ContentPart
from aware_content_ontology.part.content_part_content import ContentPartContent
from aware_content_ontology.part.content_part_enums import ContentPartType
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.stable_ids import stable_content_id

# --- AWARE: USER_IMPORTS END


async def create_content(
    key: str = "default",
    title: str | None = None,
    source: ContentSource = ContentSource.user,
    token_count: int | None = None,
    seed_inline_text: str | None = None,
    seed_part_position: int = 0,
) -> Content:
    """
    Creates a new content container.
    """

    # --- AWARE: LOGIC START create_content
    from uuid import uuid4

    content_id = stable_content_id(key=key)
    content_part_content_id = uuid4()
    content_part_text = ContentPartText(
        id=uuid4(),
        inline_text=str(seed_inline_text) if seed_inline_text is not None else "",
    )
    content_part = ContentPart(
        id=uuid4(),
        type=ContentPartType.text,
        content_part_content_id=content_part_content_id,
        content_part_text_id=content_part_text.id,
        content_part_text=content_part_text,
    )
    content_part_content = ContentPartContent(
        id=content_part_content_id,
        content_id=content_id,
        content_part_id=content_part.id,
        content_part=content_part,
        position=seed_part_position,
    )
    return Content(
        id=content_id,
        key=key,
        title=str(title) if title is not None else None,
        source=source,
        token_count=token_count,
        content_part_contents=[content_part_content],
    )
    # --- AWARE: LOGIC END create_content


async def set_title(content: Content, title: str | None = None) -> None:
    """
    Sets (or clears) the content title.
    """

    # --- AWARE: LOGIC START set_title
    content.title = str(title) if title is not None else None
    # --- AWARE: LOGIC END set_title


async def get_next_position(content: Content, content_id: UUID) -> int:
    """
    Gets the next position for a content part.
    Parameters: content_id: The UUID of the content.
    Returns: The next position for a content part.
    """

    # --- AWARE: LOGIC START get_next_position
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END get_next_position


async def increment_positions(
    content: Content, content_id: UUID, start_position: int
) -> None:
    """
    Increments the positions of content parts within a content.
    Parameters: content_id: The UUID of the content.
    start_position: The position to start incrementing from.
    """

    # --- AWARE: LOGIC START increment_positions
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END increment_positions


async def reorder_parts(
    content: Content, content_id: UUID, start_position: int, end_position: int
) -> None:
    """
    Reorders content parts within a content.
    Parameters: content_id: The UUID of the content.
    start_position: The position to start reordering from.
    end_position: The position to end reordering at.
    """

    # --- AWARE: LOGIC START reorder_parts
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END reorder_parts
