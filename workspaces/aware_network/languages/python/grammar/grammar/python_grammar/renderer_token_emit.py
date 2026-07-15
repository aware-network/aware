"""
Python token emitters (SSOT).

These helpers own the exact token/segment invariants used to materialize Python code sections.
Both one-shot renderers and surgical segment-ops should call into this layer so they never
diverge on *how* a section is shaped.
"""

from __future__ import annotations

from aware_code.section.attribute.segments import CodeSectionAttributeSegment
from aware_code.section.class_.segments import CodeSectionClassSegment
from aware_code.section.enum.segments import CodeSectionEnumSegment
from aware_code.section.enum_value.segments import CodeSectionEnumValueSegment
from aware_code.section.function.segments import CodeSectionFunctionSegment
from aware_code.section.writer import CodeSectionScope


def emit_attribute_line(
    scope: CodeSectionScope,
    *,
    name: str,
    type_annotation: str,
    default_expr: str | None,
) -> None:
    """
    Emit a single Python attribute line with canonical segments:

    - NAME
    - TYPE
    - DEFAULT_VALUE (optional)
    """
    _ = scope.token(name, CodeSectionAttributeSegment.NAME.value)
    _ = scope.token(": ")
    _ = scope.token(type_annotation, CodeSectionAttributeSegment.TYPE.value)
    if default_expr is not None:
        _ = scope.token(" = ")
        _ = scope.token(default_expr, CodeSectionAttributeSegment.DEFAULT_VALUE.value)
    _ = scope.token("\n")


def emit_class_header(
    scope: CodeSectionScope,
    *,
    name: str,
    base_name: str,
    description: str | None,
) -> None:
    """
    Emit a Python class header + optional docstring.

    Segment contract:
    - KEYWORD (optional but stable)
    - NAME (required by assembler)
    - BASES (optional but stable)
    """
    _ = scope.token("class ", CodeSectionClassSegment.KEYWORD.value)
    _ = scope.token(name, CodeSectionClassSegment.NAME.value)
    _ = scope.token("(")
    _ = scope.token(base_name, CodeSectionClassSegment.BASES.value)
    _ = scope.token("):\n")

    if not description:
        return

    desc = description.strip("\n")
    if "\n" in desc:
        _ = scope.token('    """\n')
        for line in desc.splitlines():
            _ = scope.token(f"    {line}\n")
        _ = scope.token('    """\n\n')
    else:
        _ = scope.token(f'    """{desc}"""\n\n')


def emit_enum_header(
    scope: CodeSectionScope,
    *,
    name: str,
    description: str | None,
) -> None:
    """
    Emit a Python enum header + optional docstring.

    Segment contract:
    - NAME (required by enum assembler)
    """
    _ = scope.token("class ")
    _ = scope.token(name, CodeSectionEnumSegment.NAME.value)
    _ = scope.token("(Enum):\n")

    if not description:
        return

    desc = description.strip("\n")
    with scope.indent():
        if "\n" in desc:
            _ = scope.token('"""\n')
            for line in desc.splitlines():
                _ = scope.token(f"{line}\n" if line else "\n")
            _ = scope.token('"""\n\n')
        else:
            _ = scope.token(f'"""{desc}"""\n\n')


def emit_enum_value_line(
    scope: CodeSectionScope,
    *,
    name: str,
    value_literal: str,
    description: str | None,
) -> None:
    """
    Emit a single Python enum value line with canonical segments.

    Segment contract:
    - VALUE (required by enum value assembler)
    """
    if description:
        desc = description.strip("\n")
        for line in desc.splitlines():
            if line.strip():
                _ = scope.token(f"# {line.strip()}\n")
            else:
                _ = scope.token("#\n")

    # Keep VALUE segment clean (no leading indentation).
    _ = scope.token(" " * (scope.indent_level * scope.writer.indent_size))
    _ = scope.token(name, CodeSectionEnumValueSegment.VALUE.value)
    _ = scope.token(f" = {value_literal}\n")


def emit_function_header(
    scope: CodeSectionScope,
    *,
    decorators: list[str] | None,
    name: str,
    signature: str,
    return_type: str,
    is_async: bool = False,
) -> None:
    """
    Emit a Python function header (decorators + def + signature + return type).

    Segment contract:
    - NAME (required by function assembler)
    - SIGNATURE (required by function assembler) as a single contiguous segment
    - RETURN_TYPE (optional)
    - IS_ASYNC (presence indicates async)
    """
    for deco in decorators or []:
        # Caller provides '@property', '@classmethod', etc.
        _ = scope.token(f"{deco}\n")

    if is_async:
        # Mark as async for the assembler by presence of the segment.
        _ = scope.token("async", CodeSectionFunctionSegment.IS_ASYNC.value)
        _ = scope.token(" ")

    _ = scope.token("def ")
    _ = scope.token(name, CodeSectionFunctionSegment.NAME.value)
    _ = scope.token(signature, CodeSectionFunctionSegment.SIGNATURE.value)
    _ = scope.token(" -> ")
    _ = scope.token(return_type, CodeSectionFunctionSegment.RETURN_TYPE.value)
    _ = scope.token(":\n")
