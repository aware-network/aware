from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass(slots=True)
class ORMConstructorModelProfile:
    model_validation_s: float = 0.0
    relationship_pre_validator_s: float = 0.0
    relationship_hook_guard_s: float = 0.0
    uuid_default_s: float = 0.0
    relationship_processing_s: float = 0.0
    post_init_hook_guard_s: float = 0.0
    model_validation_count: int = 0
    relationship_pre_validator_count: int = 0
    relationship_hook_guard_count: int = 0
    uuid_default_count: int = 0
    relationship_processing_count: int = 0
    post_init_hook_guard_count: int = 0


@dataclass(slots=True)
class ORMConstructorProfile:
    model_names: frozenset[str]
    models: dict[str, ORMConstructorModelProfile] = field(default_factory=dict)

    def model_profile(self, model_name: str) -> ORMConstructorModelProfile | None:
        if model_name not in self.model_names:
            return None
        profile = self.models.get(model_name)
        if profile is None:
            profile = ORMConstructorModelProfile()
            self.models[model_name] = profile
        return profile


_constructor_profile_ctx: ContextVar[ORMConstructorProfile | None] = ContextVar(
    "aware_orm_constructor_profile",
    default=None,
)


def current_orm_constructor_profile() -> ORMConstructorProfile | None:
    return _constructor_profile_ctx.get()


@contextmanager
def capture_orm_constructor_profile(
    *, model_names: Iterable[str]
) -> Iterator[ORMConstructorProfile]:
    profile = ORMConstructorProfile(model_names=frozenset(model_names))
    token = _constructor_profile_ctx.set(profile)
    try:
        yield profile
    finally:
        _constructor_profile_ctx.reset(token)


__all__ = [
    "ORMConstructorModelProfile",
    "ORMConstructorProfile",
    "capture_orm_constructor_profile",
    "current_orm_constructor_profile",
]
