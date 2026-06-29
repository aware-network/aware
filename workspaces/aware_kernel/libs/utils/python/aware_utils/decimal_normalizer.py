from decimal import Context, Decimal, ROUND_UP

# Define constants for our decimal precision
DECIMAL_PRECISION = 8
MAX_DIGITS = 20
DECIMAL_CONTEXT = Context(prec=MAX_DIGITS, rounding=ROUND_UP)


def normalize_decimal(value: Decimal) -> Decimal:
    """Normalize decimal to match database precision (20,8)."""
    # Create a Decimal for our quantum (10^-8)
    quantum = Decimal("0.00000001")  # 8 decimal places
    return value.quantize(quantum, rounding=ROUND_UP)
