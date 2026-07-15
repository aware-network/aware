from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Content Ontology
from aware_content_ontology.chain.content_chain_section import ContentChainSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def find_section_for_content(
    content_chain_section: ContentChainSection, p_content_chain_id: UUID, p_content_id: UUID
) -> UUID:
    """
    Finds the content chain section containing a specific content
    """

    # --- AWARE: LOGIC START find_section_for_content
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END find_section_for_content


async def update_newest_content_chain_content_id(
    content_chain_section: ContentChainSection,
    p_content_chain_section_id: UUID,
    p_newest_content_chain_content_id: UUID,
) -> None:
    """
    Updates the newest content chain content ID for a content chain section
    """

    # --- AWARE: LOGIC START update_newest_content_chain_content_id
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END update_newest_content_chain_content_id


async def update_oldest_content_chain_content_id(
    content_chain_section: ContentChainSection,
    p_content_chain_section_id: UUID,
    p_oldest_content_chain_content_id: UUID,
) -> None:
    """
    Updates the oldest content chain content ID for a content chain section
    """

    # --- AWARE: LOGIC START update_oldest_content_chain_content_id
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END update_oldest_content_chain_content_id
