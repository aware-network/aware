from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology.ontology.ontology_package import OntologyPackage


class ServicePackageOntologyPackage(ORMModel):
    """
    Service package to required OntologyPackage bridge.
    This records ontology packages a ServicePackage must consume through a
    Service-owned replica. The bridge is package truth so WorkspaceRevision and
    Hub consumers can reproduce required ontology replica inputs without reading
    local authoring manifests.
    """

    # Relationships
    ontology_package: OntologyPackage | None = Field(default=None)
    ontology_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    role: str = Field(default="replica")
    requirement_mode: str = Field(default="required")
    package_name: str
    fqn_prefix: str
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    service_package_id: UUID = Field(description="Foreign key for ServicePackage.ontology_packages")
    ontology_package_id: UUID = Field(description="Foreign key for ServicePackageOntologyPackage.ontology_package")
    ontology_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for ServicePackageOntologyPackage.ontology_package_object_instance_graph_commit",
    )

    @classmethod
    async def build_via_service_package(
        cls,
        service_package_id: UUID,
        ontology_package_id: UUID,
        package_name: str,
        fqn_prefix: str,
        role: str = "replica",
        requirement_mode: str = "required",
        ontology_package_object_instance_graph_commit_id: UUID | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> ServicePackageOntologyPackage:
        """
        Attach one ontology package required by this ServicePackage replica rail.

        Contract:
        - Parent `ServicePackage` scope is injected by propagation.
        - Identity is keyed by the required `OntologyPackage`.
        - `role = "replica"` means the Service consumes ontology truth through a
          local read-only projection advanced from Environment fanout.
        - `requirement_mode = "required"` means ServiceHost readiness must fail
          before handler dispatch when the replica requirement is unavailable.
        - The optional OIG commit pin lets WorkspaceRevision/Hub consumers replay
          exact ontology package truth without reopening local source manifests.
        """

        payload = {
            "service_package_id": service_package_id,
            "ontology_package_id": ontology_package_id,
            "package_name": package_name,
            "fqn_prefix": fqn_prefix,
            "role": role,
            "requirement_mode": requirement_mode,
            "ontology_package_object_instance_graph_commit_id": ontology_package_object_instance_graph_commit_id,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServicePackageOntologyPackage):
            return value
        return ServicePackageOntologyPackage.validate_invocation_value(value)


class ServicePackageOntologyPackageBuildViaServicePackageInput(BaseModel):
    service_package_id: UUID = Field(description="Foreign key for ServicePackage.ontology_packages")
    ontology_package_id: UUID
    package_name: str
    fqn_prefix: str
    role: str = Field(default="replica")
    requirement_mode: str = Field(default="required")
    ontology_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ServicePackageOntologyPackageBuildViaServicePackageOutput(BaseModel):
    value: ServicePackageOntologyPackage


FUNCTIONS = {
    "ServicePackageOntologyPackage": {
        "build_via_service_package": {
            "canonical": {
                "name": "build_via_service_package",
                "description": 'Attach one ontology package required by this ServicePackage replica rail.\n\nContract:\n- Parent `ServicePackage` scope is injected by propagation.\n- Identity is keyed by the required `OntologyPackage`.\n- `role = "replica"` means the Service consumes ontology truth through a\n  local read-only projection advanced from Environment fanout.\n- `requirement_mode = "required"` means ServiceHost readiness must fail\n  before handler dispatch when the replica requirement is unavailable.\n- The optional OIG commit pin lets WorkspaceRevision/Hub consumers replay\n  exact ontology package truth without reopening local source manifests.',
                "is_constructor": True,
            },
            "input": ServicePackageOntologyPackageBuildViaServicePackageInput,
            "output": ServicePackageOntologyPackageBuildViaServicePackageOutput,
        },
    },
}

__all__ = [
    "ServicePackageOntologyPackage",
    "ServicePackageOntologyPackageBuildViaServicePackageInput",
    "ServicePackageOntologyPackageBuildViaServicePackageOutput",
    "FUNCTIONS",
]
