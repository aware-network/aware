from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


# Enum for sorting order
class SortOrder(str, Enum):
    """Sorting order for queries"""

    ASC = "asc"
    DESC = "desc"


# Base Filter class
class BaseFilter(BaseModel):
    """Base filter class for all filters"""

    column: str
    description: Optional[str] = Field(default=None, description="Optional description for this filter")


# Specific filter types
class EqFilter(BaseFilter):
    """Filter for equality comparison"""

    value: Any = Field(..., description="Value to compare against")

    def __str__(self) -> str:
        return f"{self.column} = {self.value}"


class NeqFilter(BaseFilter):
    """Filter for inequality comparison"""

    value: Any = Field(..., description="Value to compare against")

    def __str__(self) -> str:
        return f"{self.column} != {self.value}"


class GtFilter(BaseFilter):
    """Filter for greater than comparison"""

    value: Any = Field(..., description="Value to compare against")

    def __str__(self) -> str:
        return f"{self.column} > {self.value}"


class GteFilter(BaseFilter):
    """Filter for greater than or equal comparison"""

    value: Any = Field(..., description="Value to compare against")

    def __str__(self) -> str:
        return f"{self.column} >= {self.value}"


class LtFilter(BaseFilter):
    """Filter for less than comparison"""

    value: Any = Field(..., description="Value to compare against")

    def __str__(self) -> str:
        return f"{self.column} < {self.value}"


class LteFilter(BaseFilter):
    """Filter for less than or equal comparison"""

    value: Any = Field(..., description="Value to compare against")

    def __str__(self) -> str:
        return f"{self.column} <= {self.value}"


class InFilter(BaseFilter):
    """Filter for checking if value is in a list"""

    values: list[Any] = Field(..., description="List of values to check against")

    def __str__(self) -> str:
        return f"{self.column} IN ({', '.join(str(v) for v in self.values)})"


class LikeFilter(BaseFilter):
    """Filter for string pattern matching"""

    pattern: str = Field(..., description="SQL LIKE pattern")

    def __str__(self) -> str:
        return f"{self.column} LIKE '{self.pattern}'"


class IsNullFilter(BaseFilter):
    """Filter for checking if value is NULL"""

    is_null: bool = Field(True, description="True to check for NULL, False for NOT NULL")

    def __str__(self) -> str:
        return f"{self.column} IS {'NULL' if self.is_null else 'NOT NULL'}"


class SortFilter(BaseFilter):
    """Filter for sorting results"""

    order: SortOrder = Field(default=SortOrder.ASC, description="Sort direction")

    def __str__(self) -> str:
        return f"{self.column} {self.order.value.upper()}"


# New filter type for relationship path traversal
class RelationPathFilter(BaseModel):
    """
    Filter for traversing relationships and filtering on nested fields

    This filter type allows querying based on fields in related tables and
    retrieving the parent objects. It automatically constructs the necessary
    SQL joins to traverse the relationship path.

    Example:
        To find ContentPart objects where the text segment contains "example":
        RelationPathFilter(
            path="content_part_text.content_part_text_segment",
            field="text",
            operator="like",
            value="%example%"
        )
    """

    path: str = Field(..., description="Dot-separated path of relationships to traverse")
    field: str = Field(..., description="Field name in the target table to filter on")
    operator: str = Field(
        "eq",
        description="Operator to use (eq, neq, gt, gte, lt, lte, in, like, is_null)",
    )
    value: Any = Field(..., description="Value to compare against")
    description: Optional[str] = Field(default=None, description="Optional description for this filter")

    @field_validator("path")
    def validate_path(cls, value: str) -> str:
        return normalize_path(value)

    def __str__(self) -> str:
        return f"{self.path}.{self.field} {self.operator} {self.value}"

    def get_path_segments(self) -> List[str]:
        """Get the path segments as a list"""
        return self.path.split(".")

    def to_basic_filter(self) -> BaseFilter:
        """Convert to a basic filter if possible (not normally used with RelationPathFilter)"""
        match self.operator:
            case "eq":
                return EqFilter(column=f"{self.path}.{self.field}", value=self.value)
            case "neq":
                return NeqFilter(column=f"{self.path}.{self.field}", value=self.value)
            case "gt":
                return GtFilter(column=f"{self.path}.{self.field}", value=self.value)
            case "gte":
                return GteFilter(column=f"{self.path}.{self.field}", value=self.value)
            case "lt":
                return LtFilter(column=f"{self.path}.{self.field}", value=self.value)
            case "lte":
                return LteFilter(column=f"{self.path}.{self.field}", value=self.value)
            case "in":
                return InFilter(column=f"{self.path}.{self.field}", values=self.value)
            case "like":
                return LikeFilter(column=f"{self.path}.{self.field}", pattern=self.value)
            case "is_null":
                return IsNullFilter(column=f"{self.path}.{self.field}", is_null=self.value)
            case _:
                raise ValueError(f"Unsupported operator: {self.operator}")

    def debug_info(self) -> dict:
        """Return debugging information about this filter"""
        return {
            "path": self.path,
            "normalized_path": normalize_path(self.path),
            "segments": self.get_path_segments(),
            "field": self.field,
            "operator": self.operator,
            "value": str(self.value),
        }


# Union of all filter types
FilterType = Union[
    EqFilter,
    NeqFilter,
    GtFilter,
    GteFilter,
    LtFilter,
    LteFilter,
    InFilter,
    LikeFilter,
    IsNullFilter,
    SortFilter,
    RelationPathFilter,
]


# Helper functions to create filters
def eq(column: str, value: Any) -> EqFilter:
    """Create an equality filter"""
    return EqFilter(column=column, value=value)


def neq(column: str, value: Any) -> NeqFilter:
    """Create an inequality filter"""
    return NeqFilter(column=column, value=value)


def gt(column: str, value: Any) -> GtFilter:
    """Create a greater than filter"""
    return GtFilter(column=column, value=value)


def gte(column: str, value: Any) -> GteFilter:
    """Create a greater than or equal filter"""
    return GteFilter(column=column, value=value)


def lt(column: str, value: Any) -> LtFilter:
    """Create a less than filter"""
    return LtFilter(column=column, value=value)


def lte(column: str, value: Any) -> LteFilter:
    """Create a less than or equal filter"""
    return LteFilter(column=column, value=value)


def is_in(column: str, values: List[Any]) -> InFilter:
    """Create an IN filter"""
    return InFilter(column=column, values=values)


def like(column: str, pattern: str) -> LikeFilter:
    """Create a LIKE filter"""
    return LikeFilter(column=column, pattern=pattern)


def is_null(column: str, is_null: bool = True) -> IsNullFilter:
    """Create an IS NULL filter"""
    return IsNullFilter(column=column, is_null=is_null)


def sort_by(column: str, order: SortOrder = SortOrder.ASC) -> SortFilter:
    """Create a sort filter"""
    return SortFilter(column=column, order=order)


def path_filter(path: str, field: str, operator: str, value: Any) -> RelationPathFilter:
    """
    Create a relationship path traversal filter

    Args:
        path: Dot-separated path of relationships to traverse
        field: Field name in the target table to filter on
        operator: Operator to use (eq, neq, gt, gte, lt, lte, in, like, is_null)
        value: Value to compare against

    Returns:
        A RelationPathFilter configured with the given parameters
    """
    return RelationPathFilter(path=path, field=field, operator=operator, value=value)


def path_eq(path: str, field: str, value: Any) -> RelationPathFilter:
    """Create an equality filter for a nested field"""
    return path_filter(path, field, "eq", value)


def path_neq(path: str, field: str, value: Any) -> RelationPathFilter:
    """Create an inequality filter for a nested field"""
    return path_filter(path, field, "neq", value)


def path_gt(path: str, field: str, value: Any) -> RelationPathFilter:
    """Create a greater than filter for a nested field"""
    return path_filter(path, field, "gt", value)


def path_gte(path: str, field: str, value: Any) -> RelationPathFilter:
    """Create a greater than or equal filter for a nested field"""
    return path_filter(path, field, "gte", value)


def path_lt(path: str, field: str, value: Any) -> RelationPathFilter:
    """Create a less than filter for a nested field"""
    return path_filter(path, field, "lt", value)


def path_lte(path: str, field: str, value: Any) -> RelationPathFilter:
    """Create a less than or equal filter for a nested field"""
    return path_filter(path, field, "lte", value)


def path_in(path: str, field: str, values: List[Any]) -> RelationPathFilter:
    """Create an IN filter for a nested field"""
    return path_filter(path, field, "in", values)


def normalize_path(path: str) -> str:
    """
    Normalize a relationship path by handling common path formatting issues

    This function addresses:
    1. Removes _list suffixes from segments (content_part_text_segment_list -> content_part_text_segment)
    2. Ensures consistent naming

    Args:
        path: The relationship path to normalize

    Returns:
        The normalized path
    """
    if not path:
        return path

    segments = path.split(".")
    normalized_segments = []

    for segment in segments:
        # Remove _list suffix if present
        if segment.endswith("_list"):
            segment = segment[:-5]
        normalized_segments.append(segment)

    return ".".join(normalized_segments)


def path_like(path: str, field: str, pattern: str) -> RelationPathFilter:
    """
    Create a LIKE filter for a relationship path

    Args:
        path: The relationship path (e.g., "content_part_text.content_part_text_segment")
        field: The field to filter on in the target table
        pattern: The LIKE pattern to match

    Returns:
        A RelationPathFilter configured for the LIKE operation
    """
    return RelationPathFilter(path=path, field=field, operator="like", value=pattern)


def path_is_null(path: str, field: str, is_null: bool = True) -> RelationPathFilter:
    """Create an IS NULL filter for a nested field"""
    return path_filter(path, field, "is_null", is_null)
