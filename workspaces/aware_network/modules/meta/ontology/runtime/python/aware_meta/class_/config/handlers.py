# Kernel Graph Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)

from aware_meta.graph.config.stable_ids import (
    stable_class_config_attribute_config_id,
)


def add_attribute_config(
    class_config: ClassConfig,
    attribute_config: AttributeConfig,
    position: int | None = None,
    is_identity_key: bool | None = None,
) -> None:
    """
    Add an attribute config to the class config.
    """
    position = position if position is not None else len(class_config.class_config_attribute_configs)
    identity_flag = bool(attribute_config.is_primary) if is_identity_key is None else bool(is_identity_key)
    class_config.class_config_attribute_configs.append(
        ClassConfigAttributeConfig(
            id=stable_class_config_attribute_config_id(
                class_config_id=class_config.id,
                attribute_config_id=attribute_config.id,
            ),
            class_config_id=class_config.id,
            attribute_config=attribute_config,
            attribute_config_id=attribute_config.id,
            name=attribute_config.name,
            position=position,
            is_identity_key=identity_flag,
        )
    )


def has_attr(
    class_config: ClassConfig,
    name: str,
) -> bool:
    """
    Check if an attribute with the given name exists in the class config.
    """
    for attr_config in class_config.class_config_attribute_configs:
        if attr_config.attribute_config and attr_config.attribute_config.name == name:
            return True
    return False
