from aware_meta.graph.config.stable_ids_spec.spec import (
    FunctionSpec,
    LetSpec,
    NamespaceSpec,
    ParamSpec,
    StableIdsSpec,
)
from dart_grammar.renderer_stable_ids import render_dart_stable_ids_module


def test_dart_stable_ids_renderer_uses_aware_decimal_canonical_wire() -> None:
    spec = StableIdsSpec(
        version=1,
        namespaces=(
            NamespaceSpec(
                name="NS_TEST",
                kind="ns_url",
                value="aware://test/v1",
            ),
        ),
        functions=(
            FunctionSpec(
                name="stable_exact_value_id",
                namespace="NS_TEST",
                template="aware:exact_value:{amount_text}",
                params=(ParamSpec(name="amount", type="decimal", optional=True),),
                lets=(
                    LetSpec(
                        op="decimal_text_default",
                        name="amount_text",
                        param="amount",
                        default="1.23",
                    ),
                ),
            ),
        ),
    )

    source = render_dart_stable_ids_module(spec=spec)

    assert "package:aware_model_helpers/aware_decimal.dart" in source
    assert "AwareDecimal? amount" in source
    assert "final amountText = amount?.toJson() ?? '1.23';" in source
    assert "aware:exact_value:${amountText}" in source
