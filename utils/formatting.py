from decimal import Decimal, ROUND_DOWN, getcontext
getcontext().prec = 28

def trunc1_str(x: Decimal) -> str:
    q = (x * Decimal(10)).to_integral_exact(rounding=ROUND_DOWN)
    return f"{(q / Decimal(10)):.1f}"

def trunc2_str(x: Decimal) -> str:
    q = (x * Decimal(100)).to_integral_exact(rounding=ROUND_DOWN)
    return f"{(q / Decimal(100)):.2f}"

def to_int_str(x: Decimal) -> str:
    if x <= 0:
        return "0"
    return str(int(x))
