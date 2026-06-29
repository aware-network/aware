"""
Base Model for ORM with separated concerns.

This module demonstrates a cleaner architecture where different concerns
are separated into focused mixins and components.
"""

# @doc-ref: ../../docs/models/crud.md
# @test-ref: ../../tests/models/test_crud_mixin.py

from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
from typing import ClassVar, TYPE_CHECKING, Any, Self, cast, get_args, get_origin
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, PrivateAttr, TypeAdapter, ValidationError

from aware_orm._support import logger


if TYPE_CHECKING:
    # ORM-owned graph artifact entity. Producers translate their source graph
    # models into this runtime shape before ORM binding.
    from aware_orm.runtime.graph_artifacts import OrmEntitySpec as ClassConfig

    # Aware ORM
    from aware_orm.session.session import Session
    from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata


class BaseORMModel(BaseModel):
    """
    Clean base model with only essential concerns.

    Responsibilities:
    - Core field definitions
    - Basic validation
    - ClassConfig binding
    - Session tracking

    What it DOESN'T handle (delegated to mixins):
    - CRUD operations → CRUDMixin
    - Relationships → RelationshipMixin
    - Branch awareness → BranchMixin
    - Caching → CacheMixin
    """

    # ==================== Core Fields ====================
    id: UUID = Field(default_factory=uuid4)

    # ==================== Private Attributes ====================
    _branch_id: UUID = PrivateAttr(default_factory=lambda: UUID("00000000-0000-0000-0000-000000000000"))
    _bound_session: Session | None = PrivateAttr(default=None)
    _is_new: bool = PrivateAttr(True)
    _graph_invocation_target_id: UUID | None = PrivateAttr(default=None)

    # ==================== Class Metadata ====================
    _class_config: ClassVar[ClassConfig] | None = None
    _sql_runtime_metadata: ClassVar[SQLRuntimeMetadata | None] = None

    def __init__(self, **data):
        """Initialize with session binding if available."""
        super().__init__(**data)

        cc_mod = _change_collector_module()
        try:
            is_hooks_enabled = getattr(cc_mod, "is_change_tracking_hooks_enabled", None)
            if callable(is_hooks_enabled) and not bool(is_hooks_enabled()):
                return
        except Exception:
            pass

        # Ensure list-valued fields are wrapped with change-tracked lists so
        # handler mutations (append/remove/…) can be observed without requiring
        # explicit "push" calls.
        self._wrap_list_fields_for_change_collection()

        # Allow deterministic graph construction to opt out of side-effectful
        # session binding (global identity map pollution, slow deep copies, etc.).
        try:
            autobind_mod = _autobind_module()
            is_autobind_enabled = getattr(autobind_mod, "is_autobind_enabled", None)
            if callable(is_autobind_enabled) and not bool(is_autobind_enabled()):
                return
        except Exception:
            # Default to current behavior if the guard is unavailable.
            pass

        try:
            session_ctx_mod = _current_session_ctx_module()
            current_session_context = getattr(session_ctx_mod, "current_session_context", None)
            if not callable(current_session_context):
                return
            ctx = current_session_context()
            if ctx is not None:
                session = getattr(ctx, "session", None)
                if session is not None:
                    self.bind_to_session(cast("Session", session))

        except ImportError:
            logger.debug("Current session context not available")

    @classmethod
    def validate_invocation_value(cls, value: Any) -> Self:
        """Validate runtime invocation output, allowing deferred FK-backed refs.

        Runtime may return canonical `*_id` truth for portal-backed references before
        the related object is hydrated on the Python rail. In that case, the payload is
        still authoritative; the Python facade must accept it without weakening the
        ontology-level required relationship contract.
        """
        if isinstance(value, cls):
            return value

        try:
            return cls.model_validate(value)
        except ValidationError as exc:
            patched = cls._patch_invocation_value_for_deferred_refs(value=value, exc=exc)
            if patched is None:
                raise
            patched = cls._coerce_invocation_payload_types(patched)
            instance = cls.model_construct(_fields_set=set(patched.keys()), **patched)
            instance._wrap_list_fields_for_change_collection()
            instance._autobind_from_current_session_context()
            return instance

    def _wrap_list_fields_for_change_collection(self) -> None:
        cc_mod = _change_collector_module()
        if cc_mod is None:
            return

        wrap_tracked_list = getattr(cc_mod, "wrap_tracked_list", None)
        if not callable(wrap_tracked_list):
            return

        try:
            is_tracked_list_wrapping_enabled = getattr(cc_mod, "is_tracked_list_wrapping_enabled", None)
            if callable(is_tracked_list_wrapping_enabled) and not bool(is_tracked_list_wrapping_enabled()):
                return
        except Exception:
            pass

        for field_name in type(self).model_fields:
            value = self.__dict__.get(field_name, None)
            wrapped = wrap_tracked_list(owner=self, field_name=field_name, value=value)
            if wrapped is not value:
                object.__setattr__(self, field_name, wrapped)

    def _autobind_from_current_session_context(self) -> None:
        try:
            autobind_mod = _autobind_module()
            is_autobind_enabled = getattr(autobind_mod, "is_autobind_enabled", None)
            if callable(is_autobind_enabled) and not bool(is_autobind_enabled()):
                return
        except Exception:
            pass

        try:
            session_ctx_mod = _current_session_ctx_module()
            current_session_context = getattr(session_ctx_mod, "current_session_context", None)
            if not callable(current_session_context):
                return
            ctx = current_session_context()
            if ctx is not None:
                session = getattr(ctx, "session", None)
                if session is not None:
                    self.bind_to_session(cast("Session", session))
        except ImportError:
            logger.debug("Current session context not available")

    @classmethod
    def _patch_invocation_value_for_deferred_refs(
        cls,
        *,
        value: Any,
        exc: ValidationError,
    ) -> dict[str, Any] | None:
        if not isinstance(value, Mapping):
            return None

        patched = dict(value)
        errors = exc.errors(include_url=False)
        if not errors:
            return None

        for error in errors:
            if error.get("type") != "missing":
                return None
            location = error.get("loc")
            if not isinstance(location, tuple) or not location or not isinstance(location[0], str):
                return None

            top_field_name = location[0]
            if top_field_name not in cls.model_fields:
                return None

            fk_field_name = f"{top_field_name}_id"
            if fk_field_name not in cls.model_fields or fk_field_name not in patched:
                top_value = patched.get(top_field_name)
                if len(location) > 1 and isinstance(top_value, (Mapping, list)):
                    continue
                return None

            if len(location) == 1:
                patched.setdefault(top_field_name, None)
                continue

            # A nested validation miss under a FK-backed related object still has
            # canonical identity truth at the top-level `*_id`. Defer the whole
            # related object rather than rejecting the invocation payload.
            patched[top_field_name] = None

        return patched

    @classmethod
    def _coerce_invocation_payload_types(cls, payload: dict[str, Any]) -> dict[str, Any]:
        coerced = dict(payload)
        for field_name, field_info in cls.model_fields.items():
            if field_name not in coerced:
                continue
            value = coerced[field_name]
            if value is None:
                continue
            annotation = getattr(field_info, "annotation", None)
            if annotation is None:
                continue
            nested_coerced = cls._coerce_nested_invocation_field(
                annotation=annotation,
                value=value,
            )
            if nested_coerced is not value:
                coerced[field_name] = nested_coerced
                continue
            try:
                coerced[field_name] = TypeAdapter(annotation).validate_python(value)
            except Exception:
                continue
        return coerced

    @classmethod
    def _coerce_nested_invocation_field(cls, *, annotation: Any, value: Any) -> Any:
        model_type = cls._resolve_nested_orm_model_type(annotation)
        if model_type is not None and isinstance(value, Mapping):
            return model_type.validate_invocation_value(value)

        origin = get_origin(annotation)
        if origin is list and isinstance(value, list):
            args = get_args(annotation)
            if len(args) == 1:
                item_type = cls._resolve_nested_orm_model_type(args[0])
                if item_type is not None:
                    return [
                        item
                        if isinstance(item, item_type)
                        else item_type.validate_invocation_value(item)
                        if isinstance(item, Mapping)
                        else item
                        for item in value
                    ]
        return value

    @staticmethod
    def _resolve_nested_orm_model_type(annotation: Any) -> type[BaseORMModel] | None:
        try:
            if isinstance(annotation, type) and issubclass(annotation, BaseORMModel):
                return annotation
        except TypeError:
            return None

        origin = get_origin(annotation)
        if origin is None:
            return None

        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) != 1:
            return None

        candidate = args[0]
        try:
            if isinstance(candidate, type) and issubclass(candidate, BaseORMModel):
                return candidate
        except TypeError:
            return None
        return None

    # ==================== ClassConfig Integration ====================
    @classmethod
    def bind_class_config(cls, class_config: ClassConfig) -> None:
        """Bind a ClassConfig to this model class."""
        cls._class_config = class_config

        logger.debug(f"Bound {class_config.name} to {cls.__name__}")

        # After binding, auto-register @api methods against the Python ClassConfig id (if available)
        try:
            # Iterate public callables and invoke late registration hook if present
            for attr_name in dir(cls):
                try:
                    attr = getattr(cls, attr_name)
                except Exception:
                    continue
                if callable(attr) and hasattr(attr, "__aware_register__"):
                    try:
                        # __aware_register__ expects cc_id
                        attr.__aware_register__(class_config.id)  # type: ignore[attr-defined]
                        logger.debug(f"Registered @api method {cls.__name__}.{attr_name} for CC {class_config.id}")
                    except Exception as e:
                        logger.debug(f"Skipping registration for {cls.__name__}.{attr_name}: {e}")
        except Exception as e:
            logger.debug(f"API registration skipped for {cls.__name__}: {e}")

    def get_branch_id(self) -> UUID:
        """Get the branch ID for this model."""
        return self._branch_id

    @property
    def graph_invocation_target_id(self) -> UUID:
        """Return the graph runtime target identity for instance invocations."""
        return self._graph_invocation_target_id or self.id

    def bind_graph_invocation_target_id(self, target_id: UUID) -> None:
        """Bind this ORM object to its graph-level invocation target."""
        self._graph_invocation_target_id = target_id

    @classmethod
    def get_class_config(cls) -> ClassConfig | None:
        """
        Get the ClassConfig for this model.
        """
        return cls._class_config

    @classmethod
    def ensure_class_config(cls) -> ClassConfig:
        """Ensure the ClassConfig for this model."""
        cc = cls.get_class_config()
        if cc is None:
            raise ValueError(f"No ClassConfig bound to {cls.__class__.__name__}")
        return cc

    @classmethod
    def get_sql_runtime_metadata(cls) -> SQLRuntimeMetadata | None:
        """Return manifest-derived SQL runtime metadata if available.

        Runtime installs currently populate a global registry keyed by class FQN.
        Prefer the class-local cache when present, otherwise fall back to the
        registry to keep reads consistent with write paths.
        """
        if cls._sql_runtime_metadata is not None:
            return cls._sql_runtime_metadata
        try:
            from aware_orm.runtime.sql_metadata import get_sql_metadata_for_class

            class_fqn = f"{cls.__module__}.{cls.__name__}"
            return get_sql_metadata_for_class(class_fqn)
        except Exception:
            return None

    # ==================== State Management ====================
    @property
    def is_new(self) -> bool:
        """Whether this model is new (not yet persisted)."""
        return self._is_new

    def mark_persisted(self) -> None:
        """Mark this model as persisted to the database."""
        self._is_new = False

    def mark_new(self) -> None:
        """Mark this model as new (not yet persisted)."""
        self._is_new = True

    # ==================== Session Integration ====================
    @property
    def bound_session(self) -> Session | None:
        """Get the session this model is bound to."""
        return self._bound_session

    @property
    def session(self) -> Session:
        """Get the session this model is bound to.

        Raises:
            RuntimeError: If the model is not bound to a session
        """
        if self.bound_session is None:
            raise RuntimeError("Model is not bound to a session")
        return self.bound_session

    def bind_to_session(self, session: Session) -> None:
        """Bind this model to a specific session."""
        self._bound_session = session
        try:
            # Ensure object's branch matches the session's branch before adding to identity map
            if session.branch_id is not None:
                self._branch_id = session.branch_id
        except Exception:
            pass
        session.imap_add(self)

    def ensure_session(self) -> None:
        from aware_orm.session.current_session_ctx import current_session_context

        ctx = current_session_context()
        if ctx is None:
            raise RuntimeError("No active SessionContext")
        if self.bound_session is not ctx.session or self._branch_id != ctx.branch_id:
            self.bind_to_session(ctx.session)
            self._branch_id = ctx.branch_id

    # ==================== Registry Integration ====================
    @classmethod
    def get_registry_key(cls) -> str:
        """Get the full registry key for this model."""
        return getattr(cls, "_registry_key", f"{cls.__module__}.{cls.__name__}")

    # ==================== Data Comparison Methods ====================
    def get_data_hash(self) -> str:
        """
        Get a hash of this model's data for identity comparison.

        This creates a hash based on the model's serialized data,
        excluding private attributes and session state.

        Returns:
            SHA-256 hash of the model's data
        """
        import hashlib
        import json

        # Get model data excluding private attributes and transient fields
        data = self.model_dump(exclude={"_branch_id", "_bound_session", "_is_new"})

        # Create deterministic JSON string (sorted keys)
        json_str = json.dumps(data, sort_keys=True, default=str)

        # Return SHA-256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()

    def is_data_identical(self, other: BaseORMModel) -> bool:
        """
        Check if this model has identical data to another model.

        Args:
            other: Another model instance to compare with

        Returns:
            True if the models have identical data
        """
        if not isinstance(other, BaseORMModel) or type(self) is not type(other):
            return False

        return self.get_data_hash() == other.get_data_hash()

    def get_virtual_value(self, attribute_config: AttributeConfig) -> Any:
        """Get the virtual value for this model."""
        if attribute_config.is_virtual:
            # MATCH WITH OUR INNER BASE ONEs.
            if attribute_config.name == "id":
                return self.id

    # ==================== Canonical Introspection Contract ====================
    @classmethod
    @lru_cache(maxsize=None)
    def _alias_to_field_name(cls) -> dict[str, str]:
        """Map Pydantic field aliases to their canonical field names.

        The .aware SSOT uses canonical attribute names that may be invalid identifiers in
        some language targets (e.g. `schema`). Generated models resolve these via aliases
        (e.g. `schema_` with alias `schema`). Meta builders use SSOT names, so the ORM
        introspection contract must accept either the field name or its alias.
        """
        out: dict[str, str] = {}
        for field_name, info in getattr(cls, "model_fields", {}).items():
            alias = getattr(info, "alias", None)
            if isinstance(alias, str) and alias and alias != field_name:
                out[alias] = field_name
            for extra in ("validation_alias", "serialization_alias"):
                maybe = getattr(info, extra, None)
                if isinstance(maybe, str) and maybe and maybe != field_name:
                    out.setdefault(maybe, field_name)
        return out

    def field_is_declared(self, name: str) -> bool:
        """
        Return True iff `name` is a declared Pydantic field on this model.

        This is the canonical guardrail for meta builders: they must not read
        undeclared attributes (which can trigger lazy relationship loaders via
        `__getattr__` on RelationshipMixin).
        """
        if name in type(self).model_fields:
            return True
        return name in type(self)._alias_to_field_name()

    def field_is_set(self, name: str) -> bool:
        """
        Return True iff `name` was explicitly provided (or later assigned) on this instance.

        This allows meta builders to distinguish "missing/unset" from "present but None".
        """
        if name in self.model_fields_set:
            return True
        real = type(self)._alias_to_field_name().get(name)
        if real is None:
            return False
        return real in self.model_fields_set

    def try_field_value(self, name: str, *, include_unset: bool = False) -> tuple[bool, object]:
        """
        Return (found, value) for a declared field.

        Semantics:
        - If the field is not declared -> (False, None)
        - If include_unset=False and the field is not explicitly set -> (False, None)
        - Otherwise -> (True, current_value)
        """
        if not self.field_is_declared(name):
            return False, None
        resolved = type(self)._alias_to_field_name().get(name, name)
        if not include_unset and not self.field_is_set(name):
            # Pydantic doesn't always include fields populated via `default_factory`
            # in `model_fields_set`. For canonical graph builds we treat those
            # values as present when materialized on the instance.
            field_info = type(self).model_fields.get(resolved)
            if field_info is not None and field_info.default_factory is not None:
                value = getattr(self, resolved, None)
                if value is not None:
                    return True, value
            return False, None
        return True, getattr(self, resolved)

    def try_virtual_value(self, attribute_config: AttributeConfig) -> tuple[bool, object]:
        """
        Return (found, value) for a virtual AttributeConfig.

        Virtual values are SSOT at the ORM layer; meta builders must not guess.
        """
        if not attribute_config.is_virtual:
            return False, None

        virtuals = self.get_virtual_values()
        if attribute_config.name not in virtuals:
            return False, None
        return True, virtuals[attribute_config.name]

    def try_attribute_value(self, attribute_config: AttributeConfig) -> tuple[bool, object]:
        """
        Return (found, value) for an AttributeConfig (virtual or concrete).

        This is the canonical single entrypoint used by meta builders.
        """
        if attribute_config.is_virtual:
            return self.try_virtual_value(attribute_config)
        found, value = self.try_field_value(attribute_config.name, include_unset=False)
        if not found:
            return False, None

        # Canonical determinism:
        # Treat optional explicit `None` as "missing/unset" so compiler-owned OIG commits do not
        # drift based on Pydantic `model_fields_set` differences (e.g. unset vs `field=None`)
        # across machines/CI runs.
        #
        # Required attributes must remain "present" even when their value is `None` so meta
        # builders can enforce requiredness consistently.
        if value is None and not getattr(attribute_config, "is_required", False):
            return False, None

        return True, value

    def try_class_config_id(self) -> UUID | None:
        """
        Return the bound ClassConfig.id if available.

        This is used by meta builders for optional registry indexing and reverse traversal.
        """
        cc = type(self).get_class_config()
        if cc is None:
            return None
        return cc.id

    def get_virtual_values(self) -> dict[str, Any]:
        """Get the virtual values for this model."""
        # Add default virtual values.
        virtual_values = {
            "id": self.id,
        }
        return virtual_values

    # ==================== Utility Methods ====================
    def __setattr__(self, name: str, value: Any) -> None:  # type: ignore[override]
        cc_mod = _change_collector_module()
        try:
            is_hooks_enabled = getattr(cc_mod, "is_change_tracking_hooks_enabled", None)
            if callable(is_hooks_enabled) and not bool(is_hooks_enabled()):
                return super().__setattr__(name, value)
        except Exception:
            pass

        # Never track private/internal attributes.
        if name.startswith("_"):
            return super().__setattr__(name, value)

        # Only track declared fields.
        if name not in type(self).model_fields:
            return super().__setattr__(name, value)

        if cc_mod is None:
            return super().__setattr__(name, value)

        current_change_collector = getattr(cc_mod, "current_change_collector", None)
        snapshot_list = getattr(cc_mod, "snapshot_list", None)
        wrap_tracked_list = getattr(cc_mod, "wrap_tracked_list", None)
        if not callable(current_change_collector) or not callable(snapshot_list) or not callable(wrap_tracked_list):
            return super().__setattr__(name, value)

        collector = current_change_collector()
        old_value: Any = self.__dict__.get(name, None)

        if collector is not None:
            if isinstance(old_value, list) or isinstance(value, list):
                if old_value is value:
                    pass
                else:
                    before = snapshot_list(old_value)
                    collector.record_list_mutation(obj=self, field_name=name, before=before)
                    after = snapshot_list(value) if isinstance(value, list) else []
                    collector.record_list_set(obj=self, field_name=name, before=before, after=after)
            else:
                collector.record_scalar_set(obj=self, field_name=name, old_value=old_value)

        value = wrap_tracked_list(owner=self, field_name=name, value=value)
        return super().__setattr__(name, value)

    def __str__(self) -> str:
        """Clean string representation."""
        return f"{self.__class__.__name__}(id={self.id})"

    def __repr__(self) -> str:
        """Clean representation."""
        return self.__str__()


@lru_cache(maxsize=1)
def _change_collector_module() -> Any | None:
    try:
        import aware_orm.session.change_collector as mod

        return mod
    except Exception:
        return None


@lru_cache(maxsize=1)
def _autobind_module() -> Any | None:
    try:
        import aware_orm.session.autobind as mod

        return mod
    except Exception:
        return None


@lru_cache(maxsize=1)
def _current_session_ctx_module() -> Any | None:
    try:
        import aware_orm.session.current_session_ctx as mod

        return mod
    except Exception:
        return None
