from __future__ import annotations

import importlib.util
from pathlib import Path


def test_aware_grammar_module_facade_is_removed() -> None:
    aware_grammar_root = Path(__file__).resolve().parents[1] / "aware_grammar"

    assert importlib.util.find_spec("aware_grammar.module") is None
    assert not (aware_grammar_root / "module").exists()


def test_aware_grammar_program_facade_is_removed() -> None:
    aware_grammar_root = Path(__file__).resolve().parents[1] / "aware_grammar"

    assert importlib.util.find_spec("aware_grammar.program") is None
    assert not (aware_grammar_root / "program").exists()
