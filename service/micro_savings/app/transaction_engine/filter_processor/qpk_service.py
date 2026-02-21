from typing import List, Tuple

from service.micro_savings.app.models.periods import (
    QPeriod,
    PPeriod,
    KPeriod,
)
from service.micro_savings.app.models.transaction import (
    ValidatedTransaction,
    FilteredTransaction,
    FilteredInvalidTransaction,
    AppliedQ,
    AppliedP,
)
from service.micro_savings.app.utils.date_utils import is_in_period, get_latest_start


def apply_qpk(
    transactions: List[ValidatedTransaction],
    q_periods: List[QPeriod],
    p_periods: List[PPeriod],
    k_periods: List[KPeriod],
) -> Tuple[List[FilteredTransaction], List[FilteredInvalidTransaction]]:
    """
    Apply Q, P, and K rules to each validated transaction.

    Processing order per transaction:
        1. Find all matching Q periods → pick latest start → override remanent
        2. Find all matching P periods → sum all extras → add to remanent
        3. Check all K periods → if in ANY → mark inKPeriod=True

    Transactions not in any K period → moved to invalid list.

    Returns:
        (valid_filtered, invalid_filtered)
    """
    valid: List[FilteredTransaction] = []
    invalid: List[FilteredInvalidTransaction] = []

    for tx in transactions:
        result = _apply_rules_to_transaction(tx, q_periods, p_periods, k_periods)

        if not result.inKPeriod:
            invalid.append(
                FilteredInvalidTransaction(
                    date=tx.date, amount=tx.amount, message="Not within any K period"
                )
            )
        else:
            valid.append(result)

    return valid, invalid


def _apply_rules_to_transaction(
    tx: ValidatedTransaction,
    q_periods: List[QPeriod],
    p_periods: List[PPeriod],
    k_periods: List[KPeriod],
) -> FilteredTransaction:
    """Process all three rules for a single transaction."""

    remanent = tx.remanent
    applied_q = None
    applied_p = []

    # ── Step 1: Q Rule ────────────────────────────────────────────────────────
    # Find all Q periods that contain this transaction date
    matching_q = [q for q in q_periods if is_in_period(tx.date, q.start, q.end)]

    if matching_q:
        # If multiple Q periods match, the one with the LATEST start date wins
        winning_q = get_latest_start(matching_q)
        remanent = winning_q.fixed  # Hard override
        applied_q = AppliedQ(fixed=winning_q.fixed)

    # ── Step 2: P Rule ────────────────────────────────────────────────────────
    # Find ALL P periods that contain this date, sum all extras
    matching_p = [p for p in p_periods if is_in_period(tx.date, p.start, p.end)]

    for p in matching_p:
        remanent += p.extra  # Stacking: add each one
        applied_p.append(AppliedP(extra=p.extra))

    # ── Step 3: K Rule ────────────────────────────────────────────────────────
    # Check if transaction belongs to at least one K reporting window
    in_k = any(is_in_period(tx.date, k.start, k.end) for k in k_periods)

    return FilteredTransaction(
        date=tx.date,
        amount=tx.amount,
        ceiling=tx.ceiling,
        remanent=round(remanent, 2),
        appliedQ=applied_q,
        appliedP=applied_p,
        inKPeriod=in_k,
    )


def sum_remanents_for_k_period(
    transactions: List[FilteredTransaction], k: KPeriod
) -> float:
    """
    Sum all remanents for transactions that fall within a specific K period.
    A transaction can be counted in MULTIPLE K periods — this is intentional.
    """
    total = 0.0
    for tx in transactions:
        if is_in_period(tx.date, k.start, k.end):
            total += tx.remanent
    return round(total, 2)
