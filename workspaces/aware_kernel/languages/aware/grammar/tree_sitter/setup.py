from setuptools import setup, Extension
import sys

# Define the extension module
binding_module = Extension(
    name="_binding",
    sources=[
        "tree_sitter_aware/binding.c",
        "tree_sitter_aware/src/parser.c",
        "tree_sitter_aware/src/scanner.c",
    ],
    include_dirs=["tree_sitter_aware/src"],
    define_macros=[
        ("Py_LIMITED_API", "0x03080000"),
        ("PY_SSIZE_T_CLEAN", ""),
    ],
    py_limited_api=True,
)

# If no arguments are provided (which happens with Poetry),
# inject the build_ext --inplace command
if len(sys.argv) == 1:
    sys.argv.extend(["build_ext", "--inplace"])

_ = setup(
    name="tree-sitter-aware",
    version="0.0.1",
    description="Tree-sitter grammar for the Aware language",
    author="Luis Lechuga",
    author_email="luis@aware.run",
    packages=["tree_sitter_aware"],
    package_data={
        "tree_sitter_aware": [
            "*.pyi",
            "py.typed",
            "grammar.js",
            "queries/*.scm",
        ],
    },
    ext_modules=[binding_module],
    ext_package="tree_sitter_aware",
    python_requires=">=3.12",
)
