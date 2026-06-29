from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Content Ontology
from aware_content_ontology.chain.content_chain_content import ContentChainContent

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_content_chain_content(content_chain_id: UUID, content_id: UUID, position: int) -> ContentChainContent:
    """
    Appends a Content to a ContentChain by creating a ContentChainContent edge.
    """

    # --- AWARE: LOGIC START create_content_chain_content
    from uuid import uuid4

    from aware_content_ontology.chain.content_chain_content import ContentChainContent

    return ContentChainContent(
        id=uuid4(),
        content_chain_id=content_chain_id,
        content_id=content_id,
        position=position,
    )
    # --- AWARE: LOGIC END create_content_chain_content
