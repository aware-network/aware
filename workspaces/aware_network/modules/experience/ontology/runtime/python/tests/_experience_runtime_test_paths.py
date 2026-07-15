from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[8]
AWARE_NETWORK_ROOT = REPO_ROOT / "workspaces" / "aware_network"
AWARE_KERNEL_ROOT = REPO_ROOT / "workspaces" / "aware_kernel"
EXPERIENCE_MODULE_ROOT = AWARE_NETWORK_ROOT / "modules" / "experience"
EXPERIENCE_ONTOLOGY_ROOT = EXPERIENCE_MODULE_ROOT / "ontology"
EXPERIENCE_ONTOLOGY_STRUCTURE_ROOT = EXPERIENCE_ONTOLOGY_ROOT / "structure"
EXPERIENCE_AWARE_ROOT = EXPERIENCE_ONTOLOGY_STRUCTURE_ROOT / "aware"
EXPERIENCE_ONTOLOGY_RUNTIME_ROOT = EXPERIENCE_ONTOLOGY_ROOT / "runtime" / "python"
