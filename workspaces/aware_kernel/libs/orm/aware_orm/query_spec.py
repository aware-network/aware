from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Sequence, Union

from aware_orm.filters import (
    EqFilter,
    FilterType,
    GtFilter,
    GteFilter,
    InFilter,
    IsNullFilter,
    LikeFilter,
    LtFilter,
    LteFilter,
    NeqFilter,
    RelationPathFilter,
    SortFilter,
    SortOrder,
)


FilterPredicate = Union[
    EqFilter,
    NeqFilter,
    GtFilter,
    GteFilter,
    LtFilter,
    LteFilter,
    InFilter,
    LikeFilter,
    IsNullFilter,
    RelationPathFilter,
]

_FILTER_PREDICATE_TYPES = (
    EqFilter,
    NeqFilter,
    GtFilter,
    GteFilter,
    LtFilter,
    LteFilter,
    InFilter,
    LikeFilter,
    IsNullFilter,
    RelationPathFilter,
)


@dataclass(frozen=True)
class PredicateGroup:
    """Boolean grouping for QuerySpec WHERE predicates."""

    op: Literal["and", "or"]
    predicates: tuple[Predicate, ...]

    def __post_init__(self) -> None:
        if self.op not in {"and", "or"}:
            raise ValueError("PredicateGroup op must be 'and' or 'or'")

        predicates = tuple(self.predicates)
        if not predicates:
            raise ValueError("PredicateGroup requires at least one predicate")

        for predicate in predicates:
            if not _is_predicate(predicate):
                raise TypeError(f"Unsupported QuerySpec predicate: {type(predicate).__name__}")

        object.__setattr__(self, "predicates", predicates)


Predicate = Union[FilterPredicate, PredicateGroup]


@dataclass(frozen=True)
class QueryOrder:
    """Metadata-bound ordering clause for a QuerySpec."""

    column: str
    direction: SortOrder = SortOrder.ASC

    def __post_init__(self) -> None:
        if not self.column:
            raise ValueError("QueryOrder column is required")
        if not isinstance(self.direction, SortOrder):
            object.__setattr__(self, "direction", SortOrder(str(self.direction).lower()))


@dataclass(frozen=True)
class QueryPage:
    """Limit/offset pagination for a QuerySpec."""

    limit: int | None = None
    offset: int | None = None

    def __post_init__(self) -> None:
        if self.limit is not None and self.limit < 0:
            raise ValueError("QueryPage limit must be non-negative")
        if self.offset is not None and self.offset < 0:
            raise ValueError("QueryPage offset must be non-negative")


@dataclass(frozen=True)
class QuerySpec:
    """
    Public query contract for metadata-bound SQL retrieval.

    Legacy filter lists remain supported by SQLGenerator.generate_select_many.
    QuerySpec is the strict path: predicate columns must resolve through runtime
    SQL metadata, boolean grouping is explicit, and unsupported operators fail.
    """

    where: Predicate | None = None
    order_by: tuple[QueryOrder, ...] = ()
    page: QueryPage | None = None

    def __post_init__(self) -> None:
        if self.where is not None and not _is_predicate(self.where):
            raise TypeError(f"Unsupported QuerySpec where predicate: {type(self.where).__name__}")

        order_by = tuple(self.order_by)
        for order in order_by:
            if not isinstance(order, QueryOrder):
                raise TypeError(f"Unsupported QuerySpec order: {type(order).__name__}")
        object.__setattr__(self, "order_by", order_by)

        if self.page is not None and not isinstance(self.page, QueryPage):
            raise TypeError(f"Unsupported QuerySpec page: {type(self.page).__name__}")

    @classmethod
    def from_filters(
        cls,
        filters: Sequence[FilterType] | None,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> QuerySpec:
        """Build a strict QuerySpec from the legacy flat filter-list shape."""

        filter_list = tuple(filters or ())
        order_by = tuple(
            QueryOrder(column=filter_obj.column, direction=filter_obj.order)
            for filter_obj in filter_list
            if isinstance(filter_obj, SortFilter)
        )
        predicates = tuple(filter_obj for filter_obj in filter_list if not isinstance(filter_obj, SortFilter))
        where = _group_or_single("and", predicates)
        page = QueryPage(limit=limit, offset=offset) if limit is not None or offset is not None else None
        return cls(where=where, order_by=order_by, page=page)


def and_(*predicates: Predicate) -> PredicateGroup:
    """Build an AND predicate group."""

    return PredicateGroup(op="and", predicates=tuple(predicates))


def or_(*predicates: Predicate) -> PredicateGroup:
    """Build an OR predicate group."""

    return PredicateGroup(op="or", predicates=tuple(predicates))


def _group_or_single(op: Literal["and", "or"], predicates: Iterable[Predicate]) -> Predicate | None:
    predicate_tuple = tuple(predicates)
    if not predicate_tuple:
        return None
    if len(predicate_tuple) == 1:
        return predicate_tuple[0]
    return PredicateGroup(op=op, predicates=predicate_tuple)


def _is_predicate(value: object) -> bool:
    return isinstance(value, _FILTER_PREDICATE_TYPES) or isinstance(value, PredicateGroup)


__all__ = [
    "FilterPredicate",
    "Predicate",
    "PredicateGroup",
    "QueryOrder",
    "QueryPage",
    "QuerySpec",
    "and_",
    "or_",
]
