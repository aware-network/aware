from __future__ import annotations

import pytest
from pydantic import ValidationError

from aware_orm.models.constructor_profile import (
    capture_orm_constructor_profile,
    current_orm_constructor_profile,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.session.change_collector import disable_change_tracking_hooks


class _ProfiledModel(ORMModel):
    value: int


def test_constructor_profile_is_model_filtered_and_context_scoped() -> None:
    assert current_orm_constructor_profile() is None

    with capture_orm_constructor_profile(model_names=("OtherModel",)) as profile:
        with disable_change_tracking_hooks():
            model = _ProfiledModel(value=1)

    assert model.value == 1
    assert profile.models == {}
    assert current_orm_constructor_profile() is None


def test_constructor_profile_splits_disabled_hook_validation_work() -> None:
    with capture_orm_constructor_profile(model_names=("_ProfiledModel",)) as profile:
        with disable_change_tracking_hooks():
            model = _ProfiledModel(value=1)

    metrics = profile.models["_ProfiledModel"]
    assert model.value == 1
    assert metrics.model_validation_count == 1
    assert metrics.relationship_pre_validator_count == 1
    assert metrics.relationship_hook_guard_count == 1
    assert metrics.uuid_default_count == 1
    assert metrics.relationship_processing_count == 0
    assert metrics.post_init_hook_guard_count == 1
    assert metrics.model_validation_s >= metrics.relationship_pre_validator_s
    assert metrics.relationship_pre_validator_s >= metrics.relationship_hook_guard_s
    assert metrics.relationship_hook_guard_s >= metrics.uuid_default_s
    assert metrics.post_init_hook_guard_s >= 0.0


def test_constructor_profile_records_failed_validation_without_weakening_it() -> None:
    with capture_orm_constructor_profile(model_names=("_ProfiledModel",)) as profile:
        with disable_change_tracking_hooks(), pytest.raises(ValidationError):
            _ProfiledModel(value="not-an-integer")

    metrics = profile.models["_ProfiledModel"]
    assert metrics.model_validation_count == 1
    assert metrics.relationship_pre_validator_count == 1
    assert metrics.relationship_hook_guard_count == 1
    assert metrics.uuid_default_count == 1
    assert metrics.post_init_hook_guard_count == 0
