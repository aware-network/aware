from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Content Ontology
from aware_content_ontology.part.content_part_content import ContentPartContent

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_content_part_content(content_id: UUID, content_part_id: UUID, position: int) -> ContentPartContent:
    """
    Creates a new ContentPartContent edge linking a Content to a ContentPart.
    """

    # --- AWARE: LOGIC START create_content_part_content
    from uuid import uuid4

    from aware_content_ontology.part.content_part import ContentPart
    from aware_content_ontology.part.content_part_content import ContentPartContent

    content_part = ContentPart.get_by_id_cached(content_part_id)
    if content_part is None:
        raise ValueError("ContentPart not available in write context " f"(content_part_id={content_part_id})")

    return ContentPartContent(
        id=uuid4(),
        content_id=content_id,
        content_part_id=content_part_id,
        content_part=content_part,
        position=position,
    )
    # --- AWARE: LOGIC END create_content_part_content
