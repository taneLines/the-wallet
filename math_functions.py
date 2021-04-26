from decimal import Decimal

def get_line_equation_parameters(l1, l2):
    a = Decimal((l2[1] - l1[1])) / Decimal(l2[0] - l1[0])
    b = (Decimal(l2[1]) - (a * Decimal(l2[0])))
    return float(a), float(b)