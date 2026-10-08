from __future__ import annotations

import pytest
from aware_specification_fs_adapter.markdown import MarkdownError, parse_markdown


def test_root_goal_is_exact() -> None:
    value = parse_markdown(
        "specification",
        "# Example — SPEC\n\nStatus: `draft`\nOwner: `owner`\n\n## Goal\n\nExact goal.\n",
    )
    assert value.bodies["Goal"] == "Exact goal."


@pytest.mark.parametrize("value", ["\u00a0", "\u2028", "\t"])
def test_preamble_unicode_whitespace_rejects(value: str) -> None:
    with pytest.raises(MarkdownError):
        parse_markdown(
            "specification",
            f"# Example — SPEC\n\nStatus: `draft`\nOwner: `a{value}b`\n\n## Goal\n\nGoal.\n",
        )


@pytest.mark.parametrize("value", ["\u00a0", "\u1680", "\u2028", "\x00", "\x7f"])
def test_fence_info_forbidden_codepoints_reject(value: str) -> None:
    with pytest.raises(MarkdownError):
        parse_markdown(
            "specification",
            f"# Example — SPEC\n\nStatus: `draft`\nOwner: `owner`\n\n``` {value}b\n## Goal\n```\n\n## Goal\n\nGoal.\n",
        )


def test_heading_inside_fence_is_inert() -> None:
    value = parse_markdown(
        "specification",
        "# Example — SPEC\n\nStatus: `draft`\nOwner: `owner`\n\n``` text\n## Goal\nforeign\n```\n\n## Goal\n\nExact.\n",
    )
    assert value.bodies["Goal"] == "Exact."
