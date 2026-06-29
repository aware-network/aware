from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Content Ontology
from aware_content_ontology.content.content_enums import ContentSource
from aware_content_ontology.chain.content_chain import ContentChain

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_content_ontology.content.content import Content
from aware_content_ontology.content.content_enums import ContentSource

# --- AWARE: USER_IMPORTS END


async def build(key: str = "default") -> ContentChain:
    """
    Creates a new content chain.

    Used by other modules (e.g. Conversation.build) to allocate a chain root.
    """

    # --- AWARE: LOGIC START build
    from uuid import uuid4

    from aware_content_ontology.chain.content_chain import ContentChain

    return ContentChain(id=uuid4())
    # --- AWARE: LOGIC END build


async def append_content(content_chain: ContentChain, content_id: UUID) -> UUID:
    """
    Appends a Content to this ContentChain.

    Canonical mutation boundary:
    - Callers must invoke this instance function (mutate-self-only) instead of constructing
      ContentChainContent directly from another object's handler.
    """

    # --- AWARE: LOGIC START append_content
    from aware_content_ontology.chain.content_chain_content import ContentChainContent

    position = len(content_chain.content_chain_contents_edges)
    edge = await ContentChainContent.create_content_chain_content(
        content_chain_id=content_chain.id,
        content_id=content_id,
        position=position,
    )
    return edge.id
    # --- AWARE: LOGIC END append_content


async def append_inline_text(
    content_chain: ContentChain,
    seed_inline_text: str,
    source: ContentSource = ContentSource.user,
    token_count: int | None = None,
    title: str | None = None,
) -> UUID:
    """
    Appends inline text to this ContentChain by creating Content + ContentChainContent.

    Canonical mutation boundary:
    - Parent handlers must call this instance function instead of creating Content directly.
    """

    # --- AWARE: LOGIC START append_inline_text
    content = await Content.create_content(
        title=title,
        source=source,
        token_count=token_count,
        seed_inline_text=seed_inline_text,
    )
    return await append_content(content_chain=content_chain, content_id=content.id)
    # --- AWARE: LOGIC END append_inline_text
