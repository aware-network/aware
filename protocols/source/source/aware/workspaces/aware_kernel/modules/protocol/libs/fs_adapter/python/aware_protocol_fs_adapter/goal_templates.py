"""Finite native Goal location grammar; no Goal evaluator or identity authority."""

from __future__ import annotations

import re
from datetime import date

NATIVE_GOAL_PATH_TEMPLATES = (
    "YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md",
    "goal-YYYY-MM-DD-<slug>.md",
)
_FILENAME = r"goal-(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md"


def canonical_relative_path(value: str) -> bool:
    return (
        type(value) is str
        and bool(value)
        and not any(ord(char) < 32 or ord(char) == 127 for char in value)
        and not any(char in value for char in "\\:*?<>|")
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def match_native_goal_path(template: str, tail: str) -> tuple[str, str] | None:
    """Return location date/slug only, never a verified Goal tag."""
    if template not in NATIVE_GOAL_PATH_TEMPLATES or not canonical_relative_path(tail):
        return None
    prefix = r"(?P<diryear>[0-9]{4})/(?P<dirmonth>[0-9]{2})/(?P<dirday>[0-9]{2})/" if template == NATIVE_GOAL_PATH_TEMPLATES[0] else ""
    match = re.fullmatch(prefix + _FILENAME, tail)
    if match is None:
        return None
    values = match.groupdict()
    try:
        location_date = date(int(values["year"]), int(values["month"]), int(values["day"])).isoformat()
    except ValueError:
        return None
    if prefix and any(values["dir" + name] != values[name] for name in ("year", "month", "day")):
        return None
    return location_date, values["slug"]
