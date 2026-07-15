import hashlib
from uuid import UUID

# Index
from aware_meta.graph.support.index import GraphIndex

# Member
from aware_meta.graph.support.member import T_Kind

# Reconciler
from aware_meta.graph.support.protocols.reconcile.index import GraphReconcilerIndex


def _reconciliation_fingerprint(*, kind: T_Kind, path: tuple[str, ...]) -> str:
    """
    Build a reconciliation fingerprint using the *full index path*.

    Why full path:
    - Local `GraphMember.get_path_key()` is not unique for some node kinds
      (e.g. AttributeValue nodes use a stable literal like "VALUE").
    - Using the full path makes identity stable and unambiguous under the
      canonical topologies (slot-based value trees, attribute_config_id keys, etc.).
    """
    blob = f"{getattr(kind, 'value', str(kind))}:{'/'.join(path)}"
    return hashlib.md5(blob.encode()).hexdigest()


def build_reconciler(old_idx: GraphIndex[T_Kind], new_idx: GraphIndex[T_Kind]) -> GraphReconcilerIndex:
    """Reconcile IDs between old and new graphs."""
    seen: set[UUID] = set()
    stable_id_map: dict[UUID, UUID] = {}
    # Build fingerprint -> old member id mapping
    fp_to_old_id: dict[str, UUID] = {}
    for path, (member, kind) in old_idx.get_all_paths().items():
        member_id = member.get_id()
        if member_id is None:
            raise ValueError(f"Member {member} has no ID")
        seen.add(member_id)
        fp = _reconciliation_fingerprint(kind=kind, path=path)
        fp_to_old_id[fp] = member_id

    # Map new members to old IDs where they match
    for path, (member, kind) in new_idx.get_all_paths().items():
        member_id = member.get_id()
        if member_id is None:
            raise ValueError(f"Member {member} has no ID")
        seen.add(member_id)
        fp = _reconciliation_fingerprint(kind=kind, path=path)
        old_member_id = fp_to_old_id.get(fp)
        if old_member_id is not None:
            stable_id_map[member_id] = old_member_id
    return GraphReconcilerIndex(stable_id_map=stable_id_map, seen_ids=seen)
