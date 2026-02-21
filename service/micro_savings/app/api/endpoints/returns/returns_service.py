from typing import List
from service.micro_savings.app.api.endpoints.transaction.transaction import FilteredTransaction
from service.micro_savings.app.api.endpoints.periods.periods import KPeriod
from service.micro_savings.app.api.endpoints.returns.returns import ReturnResponse, SavingsByDate
from service.micro_savings.app.api.endpoints.qpk.qpk_service import sum_remanents_for_k_period
from service.micro_savings.app.api.endpoints.tax.tax_service import compute_nps_tax_benefit

# ── Interest Rates ─────────────────────────────────────────────────────────────
NPS_RATE   = 0.0711   # 7.11% annual return for NPS
INDEX_RATE = 0.1449   # 14.49% annual return for Index Fund

MIN_YEARS_TO_RETIREMENT = 5
RETIREMENT_AGE          = 60


def compute_future_value(principal: float, rate: float, years: int) -> float:
    """
    Standard compound interest formula.

    FV = P × (1 + r)^t

    Args:
        principal: Amount invested today (INR)
        rate:      Annual interest rate as decimal (e.g. 0.0711)
        years:     Investment horizon in years

    Returns:
        Future value in INR (nominal, not inflation-adjusted)
    """
    if principal <= 0 or years <= 0:
        return 0.0
    return round(principal * ((1 + rate) ** years), 2)


def adjust_for_inflation(nominal_value: float, inflation_rate_pct: float, years: int) -> float:
    """
    Deflate a nominal future value to today's purchasing power.

    Real Value = Nominal / (1 + inflation)^t

    Args:
        nominal_value:     Future value before inflation adjustment
        inflation_rate_pct: Inflation rate as percentage (e.g. 5.5)
        years:             Number of years

    Returns:
        Real (inflation-adjusted) value in today's INR
    """
    r = inflation_rate_pct / 100
    return round(nominal_value / ((1 + r) ** years), 2)


def _years_to_retirement(age: int) -> int:
    """
    Calculate investment horizon clamped to minimum 5 years.

    Example:
        age=29  → 60-29 = 31 years
        age=57  → max(60-57, 5) = 5 years
    """
    return max(RETIREMENT_AGE - age, MIN_YEARS_TO_RETIREMENT)


def compute_returns(
    transactions:  List[FilteredTransaction],
    k_periods:     List[KPeriod],
    age:           int,
    wage:          float,
    inflation:     float,
    rate:          float,
    include_tax:   bool = False,
) -> ReturnResponse:
    """
    Core return calculation engine shared by both NPS and Index Fund endpoints.

    For each K period:
        1. Sum all remanents that fall within it
        2. Calculate future value at retirement
        3. Calculate profit (FV - principal)
        4. Optionally compute NPS tax benefit

    Args:
        transactions:  Filtered transactions with final remanent values
        k_periods:     List of K reporting windows
        age:           Investor's current age
        wage:          Monthly wage (INR)
        inflation:     Annual inflation rate (%)
        rate:          Investment return rate (NPS or Index)
        include_tax:   True for NPS (calculates tax benefit), False for Index

    Returns:
        ReturnResponse with per-K-period breakdown
    """
    years = _years_to_retirement(age)

    total_amount  = round(sum(tx.amount  for tx in transactions), 2)
    total_ceiling = round(sum(tx.ceiling for tx in transactions), 2)

    savings_by_dates: List[SavingsByDate] = []

    for k in k_periods:
        period_remanent = sum_remanents_for_k_period(transactions, k)

        future_value = compute_future_value(period_remanent, rate, years)
        profit       = round(future_value - period_remanent, 2)

        # Inflation-adjusted profit (real purchasing power gain)
        real_fv          = adjust_for_inflation(future_value, inflation, years)
        real_profit      = round(real_fv - period_remanent, 2)

        tax_benefit = 0.0
        if include_tax:
            tax_benefit = compute_nps_tax_benefit(period_remanent, wage)

        savings_by_dates.append(SavingsByDate(
            start=k.start,
            end=k.end,
            amount=period_remanent,
            profit=profit,
            taxBenefit=tax_benefit,
        ))

    return ReturnResponse(
        totalTransactionAmount=total_amount,
        totalCeiling=total_ceiling,
        savingsByDates=savings_by_dates,
    )


def compute_nps_returns(transactions, k_periods, age, wage, inflation) -> ReturnResponse:
    """Entry point for NPS returns — uses NPS rate and includes tax benefit."""
    return compute_returns(transactions, k_periods, age, wage, inflation,
                           rate=NPS_RATE, include_tax=True)


def compute_index_returns(transactions, k_periods, age, wage, inflation) -> ReturnResponse:
    """Entry point for Index Fund returns — uses index rate, no tax benefit."""
    return compute_returns(transactions, k_periods, age, wage, inflation,
                           rate=INDEX_RATE, include_tax=False)
