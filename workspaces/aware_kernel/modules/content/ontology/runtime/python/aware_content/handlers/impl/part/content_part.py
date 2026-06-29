from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Content Ontology
from aware_content_ontology.part.content_part_enums import ContentPartType
from aware_content_ontology.part.content_part import ContentPart

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from uuid import uuid4

# Content Ontology
from aware_content_ontology.part.content_part_text import ContentPartText

# --- AWARE: USER_IMPORTS END


async def create_content_part(type: ContentPartType, content_part_text_id: UUID | None = None) -> ContentPart:
    """
    Creates a new content part.
    """

    # --- AWARE: LOGIC START create_content_part
    content_part_text = None
    if content_part_text_id is not None:
        content_part_text = ContentPartText.get_by_id_cached(content_part_text_id)
        if content_part_text is None:
            raise ValueError(
                "ContentPartText not available in write context " f"(content_part_text_id={content_part_text_id})"
            )

    return ContentPart(
        id=uuid4(),
        type=type,
        content_part_text_id=content_part_text_id,
        content_part_text=content_part_text,
    )
    # --- AWARE: LOGIC END create_content_part
