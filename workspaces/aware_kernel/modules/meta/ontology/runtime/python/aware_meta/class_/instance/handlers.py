from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_attribute import ClassInstanceAttribute
from aware_meta_ontology.stable_ids import stable_class_instance_attribute_id
from aware_orm.session.autobind import disable_autobind


def link_attribute(class_instance: ClassInstance, attribute: Attribute):
    if class_instance.id is None:
        raise ValueError("ClassInstance id is required to link an Attribute")
    if attribute.id is None:
        raise ValueError("Attribute id is required to link it under a ClassInstance")

    edge_id = stable_class_instance_attribute_id(
        class_instance_id=class_instance.id,
        attribute_id=attribute.id,
    )
    for existing in class_instance.class_instance_attributes:
        if existing.id != edge_id:
            continue
        if existing.attribute is None:
            existing.attribute = attribute
            existing.attribute_id = attribute.id
        return existing

    with disable_autobind():
        edge = ClassInstanceAttribute(
            id=edge_id,
            class_instance_id=class_instance.id,
            attribute=attribute,
            attribute_id=attribute.id,
        )
    class_instance.class_instance_attributes.append(edge)
    return edge
