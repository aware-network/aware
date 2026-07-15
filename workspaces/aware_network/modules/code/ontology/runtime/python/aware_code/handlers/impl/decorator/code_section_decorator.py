from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.decorator.code_section_decorator import CodeSectionDecorator
from aware_code_ontology.decorator.code_section_decorator_expression import CodeSectionDecoratorExpression

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_expression(
    code_section_decorator: CodeSectionDecorator, position: int
) -> CodeSectionDecoratorExpression:
    """
    Create an ordered decorator-expression entry under this decorator.
    """

    # --- AWARE: LOGIC START create_expression
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_expression


async def build_via_code_section(code_section_id: UUID) -> CodeSectionDecorator:
    """
    Build the decorator payload under a CodeSection.
    """

    # --- AWARE: LOGIC START build_via_code_section
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section
