# Aware Code Experience

Code-owned view contracts for service-backed Code surfaces.

This package is the Code side of the Workspace Code-Graph workbench. Workspace
may orchestrate selection and focus, but Code owns the selector/editor view
state that represents CodePackage and source text evidence.

## Views

- `aware_code_package.codes.selector.v1` — CodePackage selector/read model.
- `aware_code_package.codes.editor.v1` — selected source text and section
  anchors.

Workspace composition must consume these views through Experience/Service view
provider bindings. It must not copy these state contracts into Workspace-owned
view DTOs.
