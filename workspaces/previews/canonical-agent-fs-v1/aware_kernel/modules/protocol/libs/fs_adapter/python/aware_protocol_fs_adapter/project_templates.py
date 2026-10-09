"""Finite Project source-locator grammar, not Project identity or target authority."""

from __future__ import annotations

import re

from .goal_templates import canonical_relative_path

PROJECT_PATH_TEMPLATE = "project-<slug>.toml"
_PROJECT_FILENAME = re.compile(r"project-([a-z0-9]+(?:-[a-z0-9]+)*)\.toml\Z")


def match_project_path(template: str, tail: str) -> str | None:
    """Return the location slug only; Project identity is record-owned."""
    if template != PROJECT_PATH_TEMPLATE or not canonical_relative_path(tail):
        return None
    match = _PROJECT_FILENAME.fullmatch(tail)
    return match.group(1) if match is not None else None
