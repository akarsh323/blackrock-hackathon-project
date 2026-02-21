import math
from typing import List, Tuple, Optional

from service.micro_savings.app.models.periods import QPeriod, PPeriod, KPeriod
from service.micro_savings.app.models.returns import ReturnResponse, SavingsByDate
from service.micro_savings.app.models.transaction import (
    RawTransaction,
    FilteredTransaction,
    AppliedQ,
    AppliedP,
)
from service.micro_savings.app.transaction_engine.tax_processor.tax_service import (
    compute_nps_tax_benefit,
)
from service.micro_savings.app.utils.date_utils import is_in_period, parse_dt

# Using explicit constants directly based on the PDF
NPS_RATE = 0.0711
INDEX_RATE = 0.1449
RETIREMENT_AGE = 60
MIN_YEARS_TO_RETIREMENT = 5


def _apply_q(
        date: str, remanent: float, q_periods: List[QPeriod]
) -> Tuple[float, Optional[AppliedQ]]:
    matching = [q for q in q_periods if is_in_period(date, q.start, q.end)]
    if not matching:
        return remanent, None
    winner = max(matching, key=lambda q: parse_dt(q.start))
    return winner.fixed, AppliedQ(fixed=winner.fixed)


def _apply_p(
        date: str, remanent: float, p_periods: List[PPeriod]
) -> Tuple[float, List[AppliedP]]:
    applied: List[AppliedP] = []
    for p in p_periods:
        if is_in_period(date, p.start, p.end):
            remanent += p.extra
            applied.append(AppliedP(extra=p.extra))
    return remanent, applied


def _build_filtered_transactions(
        raw: List[RawTransaction],
        q_periods: List[QPeriod],
        p_periods: List[PPeriod],
) -> Tuple[List[FilteredTransaction], float, float]:
    seen_dates = set()
    filtered: List[FilteredTransaction] = []
    total_amount = 0.0
    total_ceiling = 0.0

    for tx in raw:
        # 1. Reject constraint violations
        if tx.amount < 0 or tx.amount >= 500_000:
            continue

        # 2. Reject duplicate timestamps (keep only the FIRST occurrence)
        if tx.date in seen_dates:
            continue
        seen_dates.add(tx.date)

        ceil_val = math.ceil(tx.amount / 100) * 100
        rem = round(ceil_val - tx.amount, 2)

        rem, applied_q = _apply_q(tx.date, rem, q_periods)
        rem, applied_p = _apply_p(tx.date, rem, p_periods)
        rem = round(rem, 2)

        filtered.append(
            FilteredTransaction(
                date=tx.date,
                amount=tx.amount,
                ceiling=ceil_val,
                remanent=rem,
                appliedQ=applied_q,
                appliedP=applied_p,
                inKPeriod=True,
            )
        )

        total_amount += tx.amount
        total_ceiling += ceil_val

    return filtered, round(total_amount, 2), round(total_ceiling, 2)


def _years_to_retirement(age: int) -> int:
    return max(RETIREMENT_AGE - age, MIN_YEARS_TO_RETIREMENT)


def compute_future_value(principal: float, rate: float, years: int) -> float:
    if principal <= 0 or years <= 0:
        return 0.0
    return principal * ((1 + rate) ** years)


def adjust_for_inflation(nominal: float, inflation_pct: float, years: int) -> float:
    rate = inflation_pct / 100
    return nominal / ((1 + rate) ** years)


def _sum_remanents_for_k(transactions: List[FilteredTransaction], k: KPeriod) -> float:
    total = sum(
        tx.remanent for tx in transactions if is_in_period(tx.date, k.start, k.end)
    )
    return round(total, 2)


def _compute_returns_with_periods(
        raw_transactions: List[RawTransaction],
        q_periods: List[QPeriod],
        p_periods: List[PPeriod],
        k_periods: List[KPeriod],
        age: int,
        wage: float,
        inflation: float,
        rate: float,
        include_tax: bool,
) -> ReturnResponse:
    years = _years_to_retirement(age)

    filtered, total_amount, total_ceiling = _build_filtered_transactions(
        raw_transactions, q_periods, p_periods
    )

    savings_by_dates: List[SavingsByDate] = []
    for k in k_periods:
        principal = _sum_remanents_for_k(filtered, k)

        nominal_fv = compute_future_value(principal, rate, years)
        real_fv = adjust_for_inflation(nominal_fv, inflation, years)

        profit = round(real_fv - principal, 2)

        tax_benefit = compute_nps_tax_benefit(principal, wage) if include_tax else 0.0

        savings_by_dates.append(
            SavingsByDate(
                start=k.start,
                end=k.end,
                amount=principal,
                profit=profit,
                taxBenefit=tax_benefit,
            )
        )

    return ReturnResponse(
        totalTransactionAmount=total_amount,
        totalCeiling=total_ceiling,
        savingsByDates=savings_by_dates,
    )


def compute_nps_returns(
        transactions: List[RawTransaction],
        k_periods: List[KPeriod],
        q_periods: List[QPeriod],
        p_periods: List[PPeriod],
        age: int,
        wage: float,
        inflation: float,
) -> ReturnResponse:
    return _compute_returns_with_periods(
        transactions,
        q_periods,
        p_periods,
        k_periods,
        age,
        wage,
        inflation,
        rate=NPS_RATE,
        include_tax=True,
    )


def compute_index_returns(
        transactions: List[RawTransaction],
        k_periods: List[KPeriod],
        q_periods: List[QPeriod],
        p_periods: List[PPeriod],
        age: int,
        wage: float,
        inflation: float,
) -> ReturnResponse:
    return _compute_returns_with_periods(
        transactions,
        q_periods,
        p_periods,
        k_periods,
        age,
        wage,
        inflation,
        rate=INDEX_RATE,
        include_tax=False,
    )
