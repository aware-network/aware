"""Build ObjectConfigGraphOverlay when configs are provided and a canonical graph exists."""

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from aware_meta.graph.config.overlay.index import ObjectConfigGraphIndexForOverlay

from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)
from aware_meta_ontology.attribute.attribute_config_overlay import (
    AttributeConfigOverlay,
)
from aware_meta_ontology.class_.class_config_overlay import ClassConfigOverlay
from aware_meta_ontology.enum.enum_config_overlay import EnumConfigOverlay
from aware_meta_ontology.enum.enum_option_overlay import EnumOptionOverlay
from aware_meta_ontology.function.function_config_overlay import FunctionConfigOverlay

from aware_meta_ontology.annotation.code_section_annotation_overlay import (
    CodeSectionAnnotationOverlay,
)
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_utils.logging import logger

from aware_meta.graph.config.stable_ids import (
    stable_ocg_overlay_entry_id,
    stable_ocg_overlay_id,
)


def _namespace_required(value: object, *, context: str) -> str:
    namespace = getattr(value, "namespace", None)
    if not isinstance(namespace, str):
        raise ValueError(f"{context} requires namespace")
    return namespace.strip()


def _prefix_from_namespace(*, fqn_prefix: str, namespace: str) -> str:
    return f"{fqn_prefix}.{namespace}" if namespace else fqn_prefix


def build_object_config_graph_overlay_from_annotations(
    ocg: ObjectConfigGraph,
    index: ObjectConfigGraphIndexForOverlay,
    code_section_annotation_overlays: list[CodeSectionAnnotationOverlay],
    language: CodeLanguage,
) -> ObjectConfigGraphOverlay:
    """Create an ObjectConfigGraphOverlay for the given ObjectConfigGraph."""
    overlay_id = stable_ocg_overlay_id(object_config_graph_id=ocg.id, language=language.value)
    overlay = ObjectConfigGraphOverlay(
        id=overlay_id,
        language=language,
        object_config_graph_id=ocg.id,
    )

    for entry in code_section_annotation_overlays:
        prefix = _prefix_from_namespace(
            fqn_prefix=entry.fqn_prefix,
            namespace=_namespace_required(entry, context="Overlay annotation"),
        )
        if entry.entity == CodeSectionAnnotationOverlayEntity.class_:
            cls = index.classes.get(f"{prefix}.{entry.class_name}")
            if cls is None:
                raise ValueError(f"Class '{prefix}.{entry.class_name}' not found")
            overlay.class_config_overlays.append(
                ClassConfigOverlay(
                    id=stable_ocg_overlay_entry_id(overlay_id=overlay_id, kind="class", target_id=cls.id),
                    object_config_graph_overlay_id=overlay.id,
                    class_config_id=cls.id,
                    rendered_name=entry.rename,
                )
            )

        elif entry.entity == CodeSectionAnnotationOverlayEntity.enum:
            if not entry.enum_name:
                raise ValueError("enum_name is required for enum overrides")
            ec = index.enums.get(f"{prefix}.{entry.enum_name}")
            if ec is None:
                raise ValueError(f"Enum '{prefix}.{entry.enum_name}' not found")
            overlay.enum_config_overlays.append(
                EnumConfigOverlay(
                    id=stable_ocg_overlay_entry_id(overlay_id=overlay_id, kind="enum", target_id=ec.id),
                    object_config_graph_overlay_id=overlay.id,
                    enum_config_id=ec.id,
                    rendered_name=entry.rename,
                )
            )
        elif entry.entity == CodeSectionAnnotationOverlayEntity.enum_option:
            if not entry.enum_name:
                raise ValueError("enum_name is required for enum overrides")
            if not entry.enum_option_name:
                raise ValueError("enum_option_name is required for enum option overrides")
            opt = index.enum_options.get(f"{prefix}.{entry.enum_name}.{entry.enum_option_name}")
            if opt is None:
                raise ValueError(f"Enum option '{entry.enum_option_name}' not found on '{prefix}.{entry.enum_name}'")
            overlay.enum_option_overlays.append(
                EnumOptionOverlay(
                    id=stable_ocg_overlay_entry_id(overlay_id=overlay_id, kind="enum_option", target_id=opt.id),
                    object_config_graph_overlay_id=overlay.id,
                    enum_option_id=opt.id,
                    rendered_name=entry.rename,
                    wire_name=entry.wire_name,
                )
            )
        elif entry.entity == CodeSectionAnnotationOverlayEntity.attribute:
            # Support attribute overlays on:
            # - class attributes: {prefix}.{class}.{attribute}
            # - function IO attributes: {prefix}.{class}.{function}.{attribute}
            attr = None
            if entry.function_name:
                attr = index.function_attributes.get(
                    f"{prefix}.{entry.class_name}.{entry.function_name}.{entry.attribute_name}"
                )
            if attr is None:
                attr = index.attributes.get(f"{prefix}.{entry.class_name}.{entry.attribute_name}")
            if attr is None:
                # Fallback resolution: namespace_by_code_id can be incomplete for derived graphs
                # (or intentionally "unbound" in minimal graphs). If the overlay target is still
                # uniquely identifiable by suffix, bind it deterministically.
                #
                # This is especially important for overlays targeting runtime-materialized members
                # on association classes (edge endpoints).
                if entry.function_name:
                    suffix = f".{entry.class_name}.{entry.function_name}.{entry.attribute_name}"
                    matches = [a for k, a in index.function_attributes.items() if k.endswith(suffix)]
                    if len(matches) == 1:
                        attr = matches[0]
                    elif len(matches) > 1:
                        raise ValueError(
                            f"Ambiguous overlay target for function attribute '{suffix}' "
                            f"(matched {len(matches)} candidates). Use a fully-qualified path."
                        )
                else:
                    suffix = f".{entry.class_name}.{entry.attribute_name}"
                    matches = [a for k, a in index.attributes.items() if k.endswith(suffix)]
                    if len(matches) == 1:
                        attr = matches[0]
                    elif len(matches) > 1:
                        raise ValueError(
                            f"Ambiguous overlay target for attribute '{suffix}' "
                            f"(matched {len(matches)} candidates). Use a fully-qualified path."
                        )
            if attr is None:
                # Canonical extension: edge endpoint overlays are expressed from the *source* relationship path:
                # - Source::rel::Edge::member
                # - Source::rel::Edge::fn::arg
                #
                # These members are often materialized only after runtime transformation (e.g., assoc->target
                # pointer). The canonical graph will not contain them (by design), so we defer resolution.
                path = entry.source_path.strip()
                if path and len([p for p in path.split("::") if p]) >= 4:
                    logger.info(
                        f"Deferring overlay for unresolved edge endpoint attribute "
                        f"{prefix}.{entry.class_name}.{entry.attribute_name} (path={path!r}) until runtime synthesis"
                    )
                    continue
                if entry.function_name:
                    raise ValueError(
                        f"Attribute '{entry.attribute_name}' not found on "
                        f"'{prefix}.{entry.class_name}.{entry.function_name}'"
                    )
                raise ValueError(f"Attribute '{entry.attribute_name}' not found on '{prefix}.{entry.class_name}'")
            existing = next(
                (ao for ao in overlay.attribute_config_overlays if ao.attribute_config_id == attr.id),
                None,
            )
            if existing is not None:
                if entry.rename is not None:
                    if existing.rendered_name is None:
                        existing.rendered_name = entry.rename
                    elif existing.rendered_name != entry.rename:
                        raise ValueError(
                            "Conflicting attribute overlay rendered_name for "
                            f"attribute_config_id={attr.id}: {existing.rendered_name!r} vs {entry.rename!r}"
                        )
                if entry.wire_name is not None:
                    if existing.wire_name is None:
                        existing.wire_name = entry.wire_name
                    elif existing.wire_name != entry.wire_name:
                        raise ValueError(
                            "Conflicting attribute overlay wire_name for "
                            f"attribute_config_id={attr.id}: {existing.wire_name!r} vs {entry.wire_name!r}"
                        )
            else:
                overlay.attribute_config_overlays.append(
                    AttributeConfigOverlay(
                        id=stable_ocg_overlay_entry_id(overlay_id=overlay_id, kind="attribute", target_id=attr.id),
                        object_config_graph_overlay_id=overlay.id,
                        attribute_config_id=attr.id,
                        rendered_name=entry.rename,
                        wire_name=entry.wire_name,
                    )
                )
        elif entry.entity == CodeSectionAnnotationOverlayEntity.function:
            if not entry.function_name:
                raise ValueError("function_name is required for function overrides")
            fn = index.functions.get(f"{prefix}.{entry.class_name}.{entry.function_name}")
            if fn is None:
                raise ValueError(f"Function '{entry.function_name}' not found on '{prefix}.{entry.class_name}'")
            overlay.function_config_overlays.append(
                FunctionConfigOverlay(
                    id=stable_ocg_overlay_entry_id(overlay_id=overlay_id, kind="function", target_id=fn.id),
                    object_config_graph_overlay_id=overlay.id,
                    function_config_id=fn.id,
                    rendered_name=entry.rename,
                )
            )

    return overlay
