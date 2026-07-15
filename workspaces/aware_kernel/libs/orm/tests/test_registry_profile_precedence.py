from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry


class RuntimeWallet(ORMModel):
    pass


class ReadModelWallet(ORMModel):
    pass


RuntimeWallet.__module__ = "aware_test_ontology.wallet.wallet"
ReadModelWallet.__module__ = "aware_test_ontology_orm_models.wallet.wallet"


def test_runtime_model_precedes_read_model_for_shared_class_config_id() -> None:
    class_config = SimpleNamespace(id=uuid4())

    with ORMModelRegistry.temporary_clear():
        runtime_fqn = ORMModelRegistry.register_class_stub(RuntimeWallet)
        read_model_fqn = ORMModelRegistry.register_class_stub(ReadModelWallet)

        assert ORMModelRegistry.attach_class_config(read_model_fqn, class_config)
        assert (
            ORMModelRegistry.get_class_by_class_config_id(class_config.id)
            is ReadModelWallet
        )

        assert ORMModelRegistry.attach_class_config(runtime_fqn, class_config)
        assert (
            ORMModelRegistry.get_class_by_class_config_id(class_config.id)
            is RuntimeWallet
        )

        assert ORMModelRegistry.attach_class_config(read_model_fqn, class_config)
        assert (
            ORMModelRegistry.get_class_by_class_config_id(class_config.id)
            is RuntimeWallet
        )
