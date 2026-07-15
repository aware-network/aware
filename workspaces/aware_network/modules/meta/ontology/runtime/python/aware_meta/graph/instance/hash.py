import hashlib

from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta.graph.instance.index import ObjectInstanceGraphIndex
from aware_meta.attribute.instance.value.builder import fingerprint_attribute_value


def compute_hash(object_instance_graph: ObjectInstanceGraph, index: ObjectInstanceGraphIndex) -> str:
    """
    Compute a canonical content hash for an ObjectInstanceGraph.

    This hash is intended to be used for pre/post commit verification and MUST
    change for any honest world-state changes.

    Canonical coverage (v0):
    - ClassInstance membership: (class_config_id, class_instance_id)
    - Attribute values: per ClassInstance, (attribute_config_id, value_root fingerprint)
    - Relationships: (class_config_relationship_id, source_class_instance_id, target_class_instance_id)

    Intentionally excluded (v0): graph name/description and other derived metadata.
    """

    pairs: list[tuple[str, str, str]] = []

    # Canonical: deterministic ordering by (class_config_id, class_instance_id).
    class_instances = [
        ci
        for ci in object_instance_graph.class_instances
        if ci is not None and ci.class_config_id is not None and ci.id is not None
    ]
    class_instances.sort(key=lambda ci: (str(ci.class_config_id), str(ci.id)))

    for ci in class_instances:
        pairs.append(("NODE", str(ci.class_config_id), str(ci.id)))

        # Attribute values: stable identity is (class_instance_id, attribute_config_id).
        attr_rows: list[tuple[str, str]] = []
        for attr in ci.attributes:
            if attr is None or attr.attribute_config_id is None:
                continue
            root = attr.value_root
            value_fp = fingerprint_attribute_value(root) if root is not None else "missing"
            attr_rows.append((str(attr.attribute_config_id), value_fp))

        # Deterministic ordering by (attribute_config_id, value_fingerprint).
        #
        # NOTE:
        # We de-duplicate defensively, but when duplicates exist we must still be deterministic
        # across processes (set iteration order is not stable). Sorting by the full tuple keeps
        # hashing stable even if multiple rows share the same attribute_config_id.
        for attr_cfg_id, value_fp in sorted(set(attr_rows)):
            pairs.append(("ATTR", str(ci.id), f"{attr_cfg_id}:{value_fp}"))

    # Relationships: stable identity is (relationship_id, source_id, target_id).
    rel_rows_set: set[tuple[str, str, str]] = set()
    for rel in object_instance_graph.class_instance_relationships:
        if rel is None or rel.class_config_relationship_id is None:
            continue
        if rel.source_class_instance_id is None or rel.target_class_instance_id is None:
            continue
        rel_rows_set.add(
            (
                str(rel.class_config_relationship_id),
                str(rel.source_class_instance_id),
                str(rel.target_class_instance_id),
            )
        )

    for rid, src, tgt in sorted(rel_rows_set):
        pairs.append(("EDGE", rid, f"{src}->{tgt}"))

    m = hashlib.sha256()
    for k, a, b in pairs:
        m.update(k.encode("utf-8"))
        m.update(b"|")
        m.update(a.encode("utf-8"))
        m.update(b"|")
        m.update(b.encode("utf-8"))
        m.update(b"\n")
    return m.hexdigest()
