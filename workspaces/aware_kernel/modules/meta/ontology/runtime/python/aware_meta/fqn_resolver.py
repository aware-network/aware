from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, cast
from uuid import UUID

# Aware Kernel Graph Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig

# Aware Utils
from aware_utils.logging import logger


@dataclass(frozen=True, slots=True)
class NamespacePath:
    """Canonical namespace for meta symbols within a package."""

    package: str
    namespace: str

    def prefix(self) -> str:
        if not self.namespace:
            return self.package
        return f"{self.package}.{self.namespace}"

    def fqn(self, name: str) -> str:
        return f"{self.prefix()}.{name}"


def authored_ref_from_fqn(fqn: str) -> str:
    """Return the authored shorthand for a canonical package/namespace FQN."""

    parts = [part.strip() for part in fqn.split(".") if part.strip()]
    if len(parts) <= 2:
        return fqn.strip()
    return ".".join(
        [
            parts[0],
            *[part for part in parts[1:-1] if part.casefold() != "default"],
            parts[-1],
        ]
    )


class FqnRegistry:
    """Collects symbols and builds an immutable FqnResolver.

    The registry is intentionally language-agnostic: it does not interpret imports,
    aliases, or type syntax. It only assigns canonical FQNs based on package + namespace
    derived from a code_id -> namespace mapping.
    """

    def __init__(self, namespace_by_code_id: Mapping[UUID, NamespacePath]):
        self._namespace_by_code_id = dict(namespace_by_code_id)
        self._classes_by_fqn: dict[str, ClassConfig] = {}
        self._enums_by_fqn: dict[str, EnumConfig] = {}
        self._origin_code_id_by_fqn: dict[str, UUID] = {}

    def add_class(self, class_config: ClassConfig, code_id: UUID) -> str:
        ns = self._namespace_by_code_id.get(code_id)
        if ns is None:
            raise ValueError(
                f"Missing namespace for code_id={code_id} "
                + f"while registering class {class_config.name}"
            )
        fqn = ns.fqn(class_config.name)
        prev = self._classes_by_fqn.get(fqn)
        if prev is not None and prev.id != class_config.id:
            prev_origin = self._origin_code_id_by_fqn.get(fqn, "<unknown>")
            raise ValueError(
                f"Duplicate class FQN {fqn} for class_id={class_config.id} "
                + f"(prev_id={prev.id}, prev_code_id={prev_origin})"
            )
        self._classes_by_fqn[fqn] = class_config
        self._origin_code_id_by_fqn.setdefault(fqn, code_id)
        return fqn

    def add_class_with_namespace(
        self,
        class_config: ClassConfig,
        namespace: NamespacePath,
        *,
        origin_code_id: UUID | None = None,
    ) -> str:
        fqn = namespace.fqn(class_config.name)
        prev = self._classes_by_fqn.get(fqn)
        if prev is not None and prev.id != class_config.id:
            prev_origin = self._origin_code_id_by_fqn.get(fqn, "<unknown>")
            raise ValueError(
                f"Duplicate class FQN {fqn} for class_id={class_config.id} "
                + f"(prev_id={prev.id}, prev_code_id={prev_origin})"
            )
        self._classes_by_fqn[fqn] = class_config
        if origin_code_id is not None:
            self._origin_code_id_by_fqn.setdefault(fqn, origin_code_id)
        return fqn

    def add_enum(self, enum_config: EnumConfig, code_id: UUID) -> str:
        ns = self._namespace_by_code_id.get(code_id)
        if ns is None:
            raise ValueError(f"Missing namespace for code_id={code_id} while registering enum {enum_config.name}")
        fqn = ns.fqn(enum_config.name)
        prev = self._enums_by_fqn.get(fqn)
        if prev is not None and prev.id != enum_config.id:
            prev_origin = self._origin_code_id_by_fqn.get(fqn, "<unknown>")
            raise ValueError(
                f"Duplicate enum FQN {fqn} for enum_id={enum_config.id} (prev_id={prev.id}, prev_code_id={prev_origin})"
            )
        self._enums_by_fqn[fqn] = enum_config
        self._origin_code_id_by_fqn.setdefault(fqn, code_id)
        return fqn

    def add_enum_with_namespace(
        self,
        enum_config: EnumConfig,
        namespace: NamespacePath,
        *,
        origin_code_id: UUID | None = None,
    ) -> str:
        fqn = namespace.fqn(enum_config.name)
        prev = self._enums_by_fqn.get(fqn)
        if prev is not None and prev.id != enum_config.id:
            prev_origin = self._origin_code_id_by_fqn.get(fqn, "<unknown>")
            raise ValueError(
                f"Duplicate enum FQN {fqn} for enum_id={enum_config.id} (prev_id={prev.id}, prev_code_id={prev_origin})"
            )
        self._enums_by_fqn[fqn] = enum_config
        if origin_code_id is not None:
            self._origin_code_id_by_fqn.setdefault(fqn, origin_code_id)
        return fqn

    def build(self, *, imports_by_code_id: Mapping[UUID, Mapping[str, str]] | None = None) -> FqnResolver:
        return FqnResolver(
            namespace_by_code_id=self._namespace_by_code_id,
            classes_by_fqn=self._classes_by_fqn,
            enums_by_fqn=self._enums_by_fqn,
            imports_by_code_id=imports_by_code_id,
        )


class FqnResolver:
    """Immutable resolver backed by canonical FQN indexes."""

    def __init__(
        self,
        namespace_by_code_id: Mapping[UUID, NamespacePath],
        classes_by_fqn: Mapping[str, ClassConfig],
        enums_by_fqn: Mapping[str, EnumConfig],
        imports_by_code_id: Mapping[UUID, Mapping[str, str]] | None = None,
    ):
        self._namespace_by_code_id = dict(namespace_by_code_id)
        self._classes_by_fqn = dict(classes_by_fqn)
        self._enums_by_fqn = dict(enums_by_fqn)
        self._imports_by_code_id: dict[UUID, dict[str, str]] = (
            {code_id: dict(aliases) for code_id, aliases in imports_by_code_id.items()} if imports_by_code_id else {}
        )
        self._known_packages = {
            parts[0]
            for fqn in list(self._classes_by_fqn.keys()) + list(self._enums_by_fqn.keys())
            if (parts := [p for p in (fqn or "").split(".") if p])
        }

    def scope_for_code_id(self, code_id: UUID) -> FqnScope:
        ns = self._namespace_by_code_id.get(code_id)
        if ns is None:
            raise ValueError(f"Missing namespace for code_id={code_id}.")
        import_aliases = self._imports_by_code_id.get(code_id)
        return FqnScope(
            namespace=ns,
            classes_by_fqn=self._classes_by_fqn,
            enums_by_fqn=self._enums_by_fqn,
            known_packages=self._known_packages,
            import_aliases=import_aliases,
        )

    @property
    def namespace_by_code_id(self) -> Mapping[UUID, NamespacePath]:
        return self._namespace_by_code_id

    @property
    def classes_by_fqn(self) -> Mapping[str, ClassConfig]:
        return self._classes_by_fqn

    @property
    def enums_by_fqn(self) -> Mapping[str, EnumConfig]:
        return self._enums_by_fqn

    def import_aliases_for_code_id(self, code_id: UUID) -> Mapping[str, str]:
        """Return the explicit import alias table for a code unit (if any)."""
        return self._imports_by_code_id.get(code_id, {})

    def set_import_aliases_for_code_id(self, code_id: UUID, aliases: Mapping[str, str] | None) -> None:
        """Update the import alias table for a code unit (best-effort).

        This is used by editor tooling for incremental updates. If you add/remove symbol FQNs,
        rebuild the resolver instead so derived namespace indexes remain correct.
        """
        if aliases:
            self._imports_by_code_id[code_id] = dict(aliases)
        else:
            self._imports_by_code_id.pop(code_id, None)

    def update_class_config_for_fqn(self, fqn: str, class_config: ClassConfig) -> None:
        """Replace the ClassConfig payload for an existing class FQN (no key changes)."""
        if fqn in self._classes_by_fqn:
            self._classes_by_fqn[fqn] = class_config

    def update_enum_config_for_fqn(self, fqn: str, enum_config: EnumConfig) -> None:
        """Replace the EnumConfig payload for an existing enum FQN (no key changes)."""
        if fqn in self._enums_by_fqn:
            self._enums_by_fqn[fqn] = enum_config


class FqnScope:
    """Contextual resolver for a single package namespace."""

    def __init__(
        self,
        namespace: NamespacePath,
        classes_by_fqn: Mapping[str, ClassConfig],
        enums_by_fqn: Mapping[str, EnumConfig],
        known_packages: set[str] | None = None,
        import_aliases: Mapping[str, str] | None = None,
    ):
        self.namespace = namespace
        self._classes_by_fqn = classes_by_fqn
        self._enums_by_fqn = enums_by_fqn
        self._known_packages = set(known_packages or ())
        self._import_aliases = dict(import_aliases or {})

    def _normalize_import_target(self, target: str) -> str:
        normalized = (target or "").strip()
        if normalized.endswith(".*"):
            normalized = normalized.removesuffix(".*")
        return normalized

    def _expand_import_alias(self, identifier: str) -> str:
        raw = (identifier or "").strip()
        if not raw or not self._import_aliases:
            return raw

        direct = self._import_aliases.get(raw)
        if direct:
            normalized = self._normalize_import_target(direct)
            return normalized or raw

        if "." not in raw:
            return raw

        head, rest = raw.split(".", 1)
        target = self._import_aliases.get(head)
        if not target:
            return raw

        normalized = self._normalize_import_target(target)
        if not normalized:
            return raw
        return f"{normalized}.{rest}"

    def _identifiers_to_try(self, identifier: str) -> list[str]:
        raw = (identifier or "").strip()
        if not raw:
            return []
        expanded = self._expand_import_alias(raw)
        if expanded and expanded != raw:
            # Canonical precedence: try raw identifier first (local namespace), then import-expanded.
            return [raw, expanded]
        return [raw]

    def _candidate_fqns(self, identifier: str) -> list[str]:
        """
        Canonical identifier ergonomics (deterministic):

        - Name resolves only inside the current namespace.
        - namespace.Name resolves parent-relative inside the current package.
        - package.namespace.Name resolves exactly when the head is a known package.
        - No namespace pair shorthand is performed.
        """
        raw = identifier.strip()
        if not raw:
            return []

        parts = [p for p in raw.split(".") if p]
        if not parts:
            return []

        pkg = self.namespace.package
        namespace = self.namespace.namespace

        if len(parts) == 1:
            name = parts[0]
            return [f"{pkg}.{namespace}.{name}"]

        if parts[0] in self._known_packages:
            return [raw]

        namespace_parts = [part for part in namespace.split(".") if part]
        candidates: list[str] = []
        for length in range(len(namespace_parts), -1, -1):
            parent_namespace = ".".join(namespace_parts[:length])
            if parent_namespace:
                candidates.append(f"{pkg}.{parent_namespace}.{raw}")
            else:
                candidates.append(f"{pkg}.{raw}")
        candidates.append(raw)
        return list(dict.fromkeys(candidates))

    def _try_resolve_with_fqn(
        self,
        *,
        identifier: str,
        symbols_by_fqn: Mapping[str, ClassConfig | EnumConfig],
        kind_label: str,
        log_missing: bool,
    ) -> tuple[str, ClassConfig | EnumConfig] | None:
        fqn_tests: list[str] = []

        for ident in self._identifiers_to_try(identifier):
            matches: dict[str, ClassConfig | EnumConfig] = {}
            candidates = self._candidate_fqns(ident)
            for fqn in candidates:
                fqn_tests.append(fqn)
                found = symbols_by_fqn.get(fqn)
                if found is not None:
                    matches[fqn] = found

            if not matches:
                continue

            # Ambiguous match: require explicit namespace qualification.
            unique_ids = {cfg.id for cfg in matches.values()}
            if len(unique_ids) > 1:
                raise ValueError(
                    f"Ambiguous {kind_label.lower()} reference {identifier} in scope={self.namespace.prefix()}. "
                    f"Matches: {sorted(matches.keys())}"
                )

            # Single deterministic match (prefer candidate ordering)
            for fqn in candidates:
                cfg = matches.get(fqn)
                if cfg is not None:
                    return fqn, cfg

            # Should be unreachable
            fqn, cfg = next(iter(matches.items()))
            return fqn, cfg

        if log_missing:
            keys = list(symbols_by_fqn.keys())
            if len(keys) <= 50:
                all_summary = keys
            else:
                all_summary = keys[:25] + ["..."] + keys[-5:]
            logger.warning(
                f"{kind_label} not found: {identifier}. Fqns tested: {fqn_tests}. "
                f"All {kind_label.lower()}s (count={len(keys)} sample={all_summary})"
            )
        return None

    def try_resolve_class(self, identifier: str) -> ClassConfig | None:
        resolved = self._try_resolve_with_fqn(
            identifier=identifier,
            symbols_by_fqn=self._classes_by_fqn,
            kind_label="Class",
            log_missing=True,
        )
        resolved = cast(tuple[str, ClassConfig] | None, resolved)
        return resolved[1] if resolved is not None else None

    def try_resolve_class_with_fqn(self, identifier: str) -> tuple[str, ClassConfig] | None:
        """Paired form of try_resolve_class: returns (selected_fqn, ClassConfig) for persistence."""
        resolved = self._try_resolve_with_fqn(
            identifier=identifier,
            symbols_by_fqn=self._classes_by_fqn,
            kind_label="Class",
            log_missing=False,
        )
        return cast(tuple[str, ClassConfig] | None, resolved)

    def try_resolve_enum(self, identifier: str) -> EnumConfig | None:
        resolved = self._try_resolve_with_fqn(
            identifier=identifier,
            symbols_by_fqn=self._enums_by_fqn,
            kind_label="Enum",
            log_missing=False,
        )
        resolved = cast(tuple[str, EnumConfig] | None, resolved)
        return resolved[1] if resolved is not None else None

    def try_resolve_enum_with_fqn(self, identifier: str) -> tuple[str, EnumConfig] | None:
        resolved = self._try_resolve_with_fqn(
            identifier=identifier,
            symbols_by_fqn=self._enums_by_fqn,
            kind_label="Enum",
            log_missing=False,
        )
        return cast(tuple[str, EnumConfig] | None, resolved)

    def resolve_class(self, identifier: str) -> ClassConfig:
        found = self.try_resolve_class(identifier)
        if found is None:
            raise ValueError(f"Class not found: {identifier} (scope={self.namespace.prefix()})")
        return found

    def resolve_enum(self, identifier: str) -> EnumConfig:
        found = self.try_resolve_enum(identifier)
        if found is None:
            raise ValueError(f"Enum not found: {identifier} (scope={self.namespace.prefix()})")
        return found
