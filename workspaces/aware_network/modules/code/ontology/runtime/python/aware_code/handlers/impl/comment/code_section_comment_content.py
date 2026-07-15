from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.comment.code_section_comment_content import CodeSectionCommentContent

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_code_section_comment(code_section_comment_id: UUID, position: int) -> CodeSectionCommentContent:
    """
    Build an ordered comment-content item under a comment.
    """

    # --- AWARE: LOGIC START build_via_code_section_comment
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section_comment
