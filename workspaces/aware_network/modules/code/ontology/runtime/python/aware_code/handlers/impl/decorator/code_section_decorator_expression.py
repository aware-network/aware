from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.decorator.code_section_decorator_expression import CodeSectionDecoratorExpression

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_code_section_decorator(
    code_section_decorator_id: UUID, position: int = 0
) -> CodeSectionDecoratorExpression:
    """
    Build an ordered decorator-expression entry under a decorator.
    """

    # --- AWARE: LOGIC START build_via_code_section_decorator
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section_decorator
