import tomllib

import pytest
from aware_code_module_manifest_contract_runtime.python_package_setup import (
    PythonCodePackageSetup,
    render_python_code_package,
)


def test_python_profile_retains_original_names_and_requirements():
    spec = PythonCodePackageSetup(
        "hello-client", "hello_client", dependencies=("other>=1",)
    )
    files = dict(render_python_code_package(spec))
    project = tomllib.loads(files["pyproject.toml"].decode())
    assert project["project"]["name"] == "hello-client"
    assert project["project"]["dependencies"] == ["other>=1"]
    assert project["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "src/hello_client"
    ]
    assert files["src/hello_client/__init__.py"] == b'__version__ = "0.1.0"\n'


@pytest.mark.parametrize("root", ["class", "ſelf", "a.b", "../a", "hello-world", ""])
def test_import_names_refuse_before_rendering(root):
    with pytest.raises(ValueError):
        PythonCodePackageSetup("hello", root)


@pytest.mark.parametrize("distribution", ["../hello", "Hello", "hello\nworld", ""])
def test_distribution_names_refuse(distribution):
    with pytest.raises(ValueError):
        PythonCodePackageSetup(distribution, "hello")
