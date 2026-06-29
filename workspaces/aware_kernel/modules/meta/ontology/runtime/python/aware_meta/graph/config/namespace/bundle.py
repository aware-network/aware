from dataclasses import dataclass
from uuid import UUID

# Meta
from aware_meta.fqn_resolver import NamespacePath


@dataclass(frozen=True, slots=True)
class ObjectConfigGraphNamespaceBundle:
    """
    Meta-time namespace bundle keyed by meta entity IDs.

    Motivation:
    - OCG consumers (hashing, overlays, annotation semantics, render layout) must not depend on
      CodeSections/code_id once operating on an OCG. This enables:
      - synthetic classes (e.g., SQL join tables) that have no code provenance
      - distributed OCGs / OIG commits where code sections do not exist
    - Repository/build-time may still *derive* this mapping from code provenance.
    """

    namespace_by_class_config_id: dict[UUID, NamespacePath]
    namespace_by_enum_config_id: dict[UUID, NamespacePath]
    namespace_by_function_config_id: dict[UUID, NamespacePath]

    def namespace_for_class(self, class_config_id: UUID) -> NamespacePath | None:
        return self.namespace_by_class_config_id.get(class_config_id)

    def namespace_for_enum(self, enum_config_id: UUID) -> NamespacePath | None:
        return self.namespace_by_enum_config_id.get(enum_config_id)

    def namespace_for_function(self, function_config_id: UUID) -> NamespacePath | None:
        return self.namespace_by_function_config_id.get(function_config_id)
