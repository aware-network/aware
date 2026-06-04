from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field, replace
from typing import Any, Generic, TypeVar

from aware_orm.filters import (
    EqFilter,
    GtFilter,
    GteFilter,
    InFilter,
    IsNullFilter,
    LikeFilter,
    LtFilter,
    LteFilter,
    NeqFilter,
    RelationPathFilter,
    SortOrder,
)
from aware_orm.query_spec import Predicate, QueryOrder, QueryPage, QuerySpec, and_


T = TypeVar("T")


class _Unset:
    pass


_UNSET = _Unset()


class QueryFieldNamespace:
    """Descriptor exposing typed-ish field refs on generated ORM models."""

    def __get__(self, instance: object, owner: type | None = None) -> BoundQueryFields:
        if owner is None:
            raise AttributeError("Query field refs must be accessed from a model class")
        return BoundQueryFields(owner)


@dataclass(frozen=True)
class BoundQueryFields:
    model: type

    def __getattr__(self, name: str) -> QueryField:
        if name.startswith("_"):
            raise AttributeError(name)
        return QueryField(name)

    def __getitem__(self, name: str) -> QueryField:
        return self.field(name)

    def field(self, name: str) -> QueryField:
        return QueryField(name)

    def relation(self, path: str) -> QueryRelationPath:
        return QueryRelationPath(path)

    def path(self, path: str, field: str) -> QueryRelationField:
        return QueryRelationField(path=path, field=field)


@dataclass(frozen=True)
class QueryField:
    column: str

    def eq(self, value: Any) -> EqFilter:
        return EqFilter(column=self.column, value=value)

    def neq(self, value: Any) -> NeqFilter:
        return NeqFilter(column=self.column, value=value)

    def gt(self, value: Any) -> GtFilter:
        return GtFilter(column=self.column, value=value)

    def gte(self, value: Any) -> GteFilter:
        return GteFilter(column=self.column, value=value)

    def lt(self, value: Any) -> LtFilter:
        return LtFilter(column=self.column, value=value)

    def lte(self, value: Any) -> LteFilter:
        return LteFilter(column=self.column, value=value)

    def in_(self, values: list[Any] | tuple[Any, ...]) -> InFilter:
        return InFilter(column=self.column, values=list(values))

    def like(self, pattern: str) -> LikeFilter:
        return LikeFilter(column=self.column, pattern=pattern)

    def is_null(self, is_null: bool = True) -> IsNullFilter:
        return IsNullFilter(column=self.column, is_null=is_null)

    def asc(self) -> QueryOrder:
        return QueryOrder(column=self.column, direction=SortOrder.ASC)

    def desc(self) -> QueryOrder:
        return QueryOrder(column=self.column, direction=SortOrder.DESC)


@dataclass(frozen=True)
class QueryRelationPath:
    path: str

    def __getattr__(self, field: str) -> QueryRelationField:
        if field.startswith("_"):
            raise AttributeError(field)
        return self.field(field)

    def field(self, field: str) -> QueryRelationField:
        return QueryRelationField(path=self.path, field=field)


@dataclass(frozen=True)
class QueryRelationField:
    path: str
    field: str

    def eq(self, value: Any) -> RelationPathFilter:
        return self._filter("eq", value)

    def neq(self, value: Any) -> RelationPathFilter:
        return self._filter("neq", value)

    def gt(self, value: Any) -> RelationPathFilter:
        return self._filter("gt", value)

    def gte(self, value: Any) -> RelationPathFilter:
        return self._filter("gte", value)

    def lt(self, value: Any) -> RelationPathFilter:
        return self._filter("lt", value)

    def lte(self, value: Any) -> RelationPathFilter:
        return self._filter("lte", value)

    def in_(self, values: list[Any] | tuple[Any, ...]) -> RelationPathFilter:
        return self._filter("in", list(values))

    def like(self, pattern: str) -> RelationPathFilter:
        return self._filter("like", pattern)

    def is_null(self, is_null: bool = True) -> RelationPathFilter:
        return self._filter("is_null", is_null)

    def _filter(self, operator: str, value: Any) -> RelationPathFilter:
        return RelationPathFilter(path=self.path, field=self.field, operator=operator, value=value)


@dataclass(frozen=True)
class ModelQuery(Generic[T]):
    """Fluent generated-model query builder compiled to QuerySpec."""

    model: type[T]
    query_spec: QuerySpec = dataclass_field(default_factory=QuerySpec)
    cache_valid: bool = True

    def where(self, *predicates: Predicate) -> ModelQuery[T]:
        return self._with(where=_and_where(self.query_spec.where, predicates))

    def order_by(self, *orders: QueryOrder | QueryField) -> ModelQuery[T]:
        normalized: list[QueryOrder] = []
        for order in orders:
            if isinstance(order, QueryField):
                normalized.append(order.asc())
            elif isinstance(order, QueryOrder):
                normalized.append(order)
            else:
                raise TypeError(f"Unsupported query order: {type(order).__name__}")
        return self._with(order_by=tuple(normalized))

    def limit(self, limit: int | None) -> ModelQuery[T]:
        page = self.query_spec.page or QueryPage()
        return self._with(page=replace(page, limit=limit))

    def offset(self, offset: int | None) -> ModelQuery[T]:
        page = self.query_spec.page or QueryPage()
        return self._with(page=replace(page, offset=offset))

    def page(self, *, limit: int | None = None, offset: int | None = None) -> ModelQuery[T]:
        return self._with(page=QueryPage(limit=limit, offset=offset))

    def spec(self) -> QuerySpec:
        return self.query_spec

    async def all(self) -> list[T]:
        return await self.model._query_spec(self.query_spec, cache_valid=self.cache_valid)

    async def first(self) -> T | None:
        rows = await self.limit(1).all()
        return rows[0] if rows else None

    async def count(self) -> int:
        return await self.model.count_query(self.query_spec)

    def _with(
        self,
        *,
        where: Predicate | None | object = _UNSET,
        order_by: tuple[QueryOrder, ...] | object = _UNSET,
        page: QueryPage | None | object = _UNSET,
    ) -> ModelQuery[T]:
        return replace(
            self,
            query_spec=replace(
                self.query_spec,
                where=self.query_spec.where if where is _UNSET else where,
                order_by=self.query_spec.order_by if order_by is _UNSET else order_by,
                page=self.query_spec.page if page is _UNSET else page,
            ),
        )


def _and_where(existing: Predicate | None, predicates: tuple[Predicate, ...]) -> Predicate | None:
    parts = tuple(part for part in ((existing,) + predicates) if part is not None)
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return and_(*parts)


__all__ = [
    "BoundQueryFields",
    "ModelQuery",
    "QueryField",
    "QueryFieldNamespace",
    "QueryRelationField",
    "QueryRelationPath",
]
