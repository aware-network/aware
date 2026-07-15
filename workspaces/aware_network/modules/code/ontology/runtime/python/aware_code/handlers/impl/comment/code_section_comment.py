from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.comment.code_section_comment_enums import CodeSectionCommentType
from aware_code_ontology.comment.code_section_comment import CodeSectionComment
from aware_code_ontology.comment.code_section_comment_content import CodeSectionCommentContent

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_content(code_section_comment: CodeSectionComment, position: int) -> CodeSectionCommentContent:
    """
    Create an ordered comment-content item under this comment.
    """

    # --- AWARE: LOGIC START create_content
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_content


async def build_via_code_section(code_section_id: UUID, type: CodeSectionCommentType) -> CodeSectionComment:
    """
    Build the comment payload under a CodeSection.
    """

    # --- AWARE: LOGIC START build_via_code_section
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section
