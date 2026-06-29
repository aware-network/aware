from __future__ import annotations

from uuid import UUID

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_meta.class_.config.builder import build_class_config_from_code
from aware_meta.enum.config.builder import build_enum_config_from_code
from aware_meta.fqn_resolver import FqnRegistry, FqnResolver, NamespacePath
from aware_meta.graph.config.builder import build_import_aliases_by_code_id


def build_symbol_resolver(
    *,
    file_codes: list[tuple[str, Code]],
    namespace_by_code_id: dict[UUID, NamespacePath],
) -> FqnResolver:
    """Build a best-effort resolver for editor features.

    This intentionally avoids full OCG construction so a single unresolved relationship
    does not prevent basic navigation (definition/hover/completion) from working.
    """
    imports_by_code_id = build_import_aliases_by_code_id(file_codes)

    enum_configs: list[EnumConfig] = []
    class_configs: list[ClassConfig] = []
    for _, code in file_codes:
        for section in code.code_sections:
            if section.type == CodeSectionType.enum and section.code_section_enum is not None:
                code_id = section.code_section_enum.code_section.code_id
                ns = namespace_by_code_id.get(code_id)
                if ns is None:
                    continue
                enum_configs.append(
                    build_enum_config_from_code(code_section_enum=section.code_section_enum, namespace=ns)
                )
            if section.type == CodeSectionType.class_ and section.code_section_class is not None:
                class_configs.append(build_class_config_from_code(section.code_section_class, parent_class_id=None))

    registry = FqnRegistry(namespace_by_code_id)
    for enum_config in enum_configs:
        if enum_config.code_section_enum is None:
            continue
        try:
            registry.add_enum(enum_config, enum_config.code_section_enum.code_section.code_id)
        except ValueError:
            continue

    for class_config in class_configs:
        if class_config.code_section_class is None:
            continue
        try:
            registry.add_class(class_config, class_config.code_section_class.code_section.code_id)
        except ValueError:
            continue

    # Build a base resolver first so mirror directives can resolve their targets against the
    # dependency-closed workspace snapshot (ontology + api packages).
    base_resolver = registry.build(imports_by_code_id=imports_by_code_id)

    # Mirrors are file-level API directives that alias an external symbol into the local namespace.
    # For editor features we register the mirrored target under the local namespace so type
    # resolution works (and can jump to the ontology definition via shared config objects).
    for _, code in file_codes:
        for section in code.code_sections:
            if section.type != CodeSectionType.mirror or section.code_section_mirror is None:
                continue
            mirror = section.code_section_mirror
            code_id = mirror.code_section.code_id
            ns = namespace_by_code_id.get(code_id)
            if ns is None:
                continue

            scope = base_resolver.scope_for_code_id(code_id)
            target = (mirror.target_text or "").strip()
            if not target:
                continue

            enum_cfg = scope.try_resolve_enum(target)
            if enum_cfg is not None:
                try:
                    registry.add_enum_with_namespace(enum_cfg, ns, origin_code_id=code_id)
                except ValueError:
                    pass
                continue

            class_resolved = scope.try_resolve_class_with_fqn(target)
            if class_resolved is None:
                continue
            _, class_cfg = class_resolved
            try:
                registry.add_class_with_namespace(class_cfg, ns, origin_code_id=code_id)
            except ValueError:
                pass

    return registry.build(imports_by_code_id=imports_by_code_id)
