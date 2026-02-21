def compute_tax(annual_income: float) -> float:
    """
    Calculate Indian income tax based on new tax regime slabs (FY 2023-24).

    Slabs:
        ₹0          – ₹7,00,000   →  0%
        ₹7,00,001   – ₹10,00,000  → 10%  on amount above ₹7L
        ₹10,00,001  – ₹12,00,000  → 15%  on amount above ₹10L
        ₹12,00,001  – ₹15,00,000  → 20%  on amount above ₹12L
        ₹15,00,001  → ∞           → 30%  on amount above ₹15L

    Args:
        annual_income: Gross annual income in INR

    Returns:
        Tax amount in INR (float)

    Examples:
        compute_tax(600_000)   → 0.0
        compute_tax(800_000)   → 10_000.0   (10% of 1L above 7L)
        compute_tax(1_200_000) → 65_000.0
    """
    tax = 0.0

    slabs = [
        (700_000, 0.00),
        (1_000_000, 0.10),
        (1_200_000, 0.15),
        (1_500_000, 0.20),
        (float("inf"), 0.30),
    ]

    prev_limit = 0
    for limit, rate in slabs:
        if annual_income <= prev_limit:
            break
        taxable = min(annual_income, limit) - prev_limit
        tax += taxable * rate
        prev_limit = limit

    return round(tax, 2)


def compute_nps_tax_benefit(total_invested: float, monthly_wage: float) -> float:
    """
    Calculate tax saved by investing via NPS under Section 80CCD(1B).

    NPS allows deduction of:
        min(total_invested, 10% of annual_wage, ₹2,00,000)

    The benefit = tax on full income MINUS tax on (income - deduction)

    Args:
        total_invested: Total remanent amount put into NPS
        monthly_wage:   Monthly salary in INR

    Returns:
        Tax benefit in INR

    Example:
        wage=50,000/month → annual=6,00,000
        invested=10,000
        max_deduction = min(10000, 60000, 200000) = 10000
        benefit = tax(600000) - tax(590000) = 0 - 0 = 0  (below 7L slab)
    """
    annual_wage = monthly_wage * 12
    max_deduction = min(total_invested, annual_wage * 0.10, 200_000)

    tax_before = compute_tax(annual_wage)
    tax_after = compute_tax(annual_wage - max_deduction)

    benefit = tax_before - tax_after
    return round(max(benefit, 0.0), 2)  # Never negative
