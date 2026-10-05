"""Issue-owned projection of authored, versioned consumer templates."""
import argparse
import ast
import hashlib
import html
import json
from pathlib import Path
import shlex


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-public", action="store_true", help="Render this public repository's bootstrap and modules; producer Issue scope required.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = root / "protocols/contracts/agent-fs/v1"
    target = root / "protocols/agent/source/aware_agent_cli/aware_agent_cli/templates/agent-fs-v1"
    metadata_bytes = (source / "contract.json").read_bytes()
    metadata = json.loads(metadata_bytes)
    target.mkdir(parents=True, exist_ok=True)
    (target / "contract.json").write_bytes(metadata_bytes)
    templates = {}
    for name, relative in metadata["files"].items():
        data = (source / relative).read_bytes()
        templates[name] = data
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    if args.render_public:
        outputs = {}
        for name, data in templates.items():
            text = data.decode().replace("{{AWARE_COMMAND_MARKDOWN}}", "<code>aware</code>").replace("{{AWARE_COMMAND_SHELL}}", shlex.quote("aware")).replace("{{DOCS_PREFIX}}", "docs")
            outputs[name] = text.encode()
        outputs[".aware/agent-protocol.md"] = templates["AGENTS.md"].decode().replace("{{AWARE_COMMAND_MARKDOWN}}", "<code>aware</code>").replace("{{AWARE_COMMAND_SHELL}}", shlex.quote("aware")).replace("{{DOCS_PREFIX}}", "../docs").encode()
        tree = ast.parse((root / "protocols/agent/source/aware_agent_cli/aware_agent_cli/main.py").read_bytes())
        manifest = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MANIFEST" for t in n.targets))
        outputs["aware.protocol.toml"] = manifest.encode()
        record = {"contract_ref": metadata["contract_ref"], "version": metadata["version"], "command": "aware",
                  "template_sha256": {n: hashlib.sha256(b).hexdigest() for n, b in templates.items()},
                  "rendered_sha256": {n: hashlib.sha256(b).hexdigest() for n, b in outputs.items()},
                  "qualification": "Public repository dogfoods the consumer filesystem profile. Setup provenance, not actor authority; no internal RepositoryRevision/workspace manifest."}
        outputs[".aware/agent-bootstrap.json"] = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
        for name, data in outputs.items():
            path = root / name
            if path.is_symlink():
                raise ValueError("public_render_symlink_refused:" + name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        print(json.dumps({"contract_ref": metadata["contract_ref"], "version": metadata["version"], "rendered": len(outputs)}))
    else:
        print(json.dumps({"contract_ref": metadata["contract_ref"], "version": metadata["version"], "packaged": len(templates)}))


if __name__ == "__main__":
    main()
