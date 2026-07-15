# @code-under-test: ../../aware_orm/cache/identity_map.py

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


from aware_orm.cache.identity_map import IdentityMap, SessionScopedIdentityMap
from aware_orm.helpers import MAIN_BRANCH_ID


@dataclass
class DummyModel:
    """Simple model stub to control identity-map behaviour."""

    id: UUID
    data: dict[str, str]
    branch_id: UUID = MAIN_BRANCH_ID

    def get_branch_id(self) -> UUID:
        return self.branch_id

    def is_data_identical(self, other: DummyModel) -> bool:
        return self.data == other.data

    def get_data_hash(self) -> str:
        return "|".join(f"{k}:{v}" for k, v in sorted(self.data.items()))


def make_model(
    data: dict[str, str] | None = None,
    branch: UUID | None = None,
    *,
    id_value: UUID | None = None,
):
    return DummyModel(
        id=id_value or uuid4(),
        data=data or {},
        branch_id=branch or MAIN_BRANCH_ID,
    )


class TestIdentityMapCore:
    def test_add_get_contains_and_remove(self):
        imap = IdentityMap()
        model = make_model({"name": "primary"})

        assert imap.get(DummyModel, model.id) is None
        imap.add(model)

        assert imap.contains(DummyModel, model.id)
        assert imap.get(DummyModel, model.id) is model
        assert imap.size() == 1

        removed = imap.remove(DummyModel, model.id)
        assert removed is model
        assert imap.size() == 0

    def test_duplicate_identical_data_keeps_original_instance(self):
        shared_id = uuid4()
        original = make_model({"field": "value"}, id_value=shared_id)
        identical = make_model({"field": "value"}, id_value=shared_id)

        imap = IdentityMap()
        imap.add(original)
        imap.add(identical)  # identical payload → reuse original

        cached = imap.get(DummyModel, shared_id)
        assert cached is original  # existing instance retained
        assert imap.size() == 1

    def test_duplicate_different_data_replaces_existing(self):
        shared_id = uuid4()
        original = make_model({"field": "value"}, id_value=shared_id)
        replacement = make_model({"field": "updated"}, id_value=shared_id)

        imap = IdentityMap()
        imap.add(original)
        imap.add(replacement)

        cached = imap.get(DummyModel, shared_id)
        assert cached is replacement  # replacement wins
        assert imap.size() == 1

    def test_statistics_report_counts(self):
        imap = IdentityMap()
        models = [make_model({"idx": str(i)}) for i in range(3)]
        for model in models:
            imap.add(model)

        stats = imap.get_statistics()
        assert stats["total_objects"] == 3
        assert stats["type_counts"]["DummyModel"] == 3

    def test_clear_removes_all_objects(self):
        imap = IdentityMap()
        imap.add(make_model({}))
        imap.add(make_model({}))

        imap.clear()
        assert imap.size() == 0
        assert imap.get_statistics()["total_objects"] == 0


class TestSessionScopedIdentityMap:
    def test_branch_awareness_and_stats(self):
        branch = uuid4()
        imap = SessionScopedIdentityMap(branch_id=branch)
        model = make_model({"value": "branch"}, branch=branch)

        imap.add(model)
        stats = imap.get_statistics()

        assert stats["total_objects"] == 1
        assert stats["branch_id"] == str(branch)
        assert stats["is_main_branch"] is False

    def test_branch_warning_does_not_block_add(self, caplog):
        branch = uuid4()
        imap = SessionScopedIdentityMap(branch_id=branch)
        mismatched = make_model({"value": "wrong"}, branch=MAIN_BRANCH_ID)

        imap.add(mismatched)

        assert imap.contains(DummyModel, mismatched.id)
        assert any("differs from identity map branch" in record.message for record in caplog.records)
