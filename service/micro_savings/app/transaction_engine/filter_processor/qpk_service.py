import math
from typing import List, Tuple, Set

from service.micro_savings.app.models.filter import FilterInputTransaction
from service.micro_savings.app.models.periods import QPeriod, PPeriod, KPeriod
from service.micro_savings.app.models.transaction import (
    FilteredTransaction,
    FilteredInvalidTransaction,
    AppliedQ,
    AppliedP,
)
from service.micro_savings.app.utils.date_utils import is_in_period, get_latest_start


# ── Ceiling / Remanent helpers ────────────────────────────────────────────────


def _compute_ceiling(amount: float) -> float:
    """
    Next multiple of 100 at or above amount.
    e.g. 375 → 400, 400 → 400, 620 → 700
    """
    return math.ceil(amount / 100) * 100


def _compute_remanent(amount: float, ceiling: float) -> float:
    return round(ceiling - amount, 2)


# ── Main entry point ──────────────────────────────────────────────────────────


def apply_qpk(
        transactions: List[FilterInputTransaction],
        q_periods: List[QPeriod],
        p_periods: List[PPeriod],
        k_periods: List[KPeriod],
) -> Tuple[List[FilteredTransaction], List[FilteredInvalidTransaction]]:
    """
    Full filter pipeline per transaction:

        Pre-check : reject negatives and duplicates (spec: tᵢ ≠ tⱼ, x ≥ 0)
        Step 1    : compute ceiling and remanent from amount
        Step 2    : apply Q rule  (latest-start wins; hard override)
        Step 3    : apply P rule  (all matching extras stack)
        Step 4    : apply K rule  (must fall in at least one K window)

    Returns:
        (valid_filtered, invalid_filtered)
    """
    valid: List[FilteredTransaction] = []
    invalid: List[FilteredInvalidTransaction] = []
    seen_dates: Set[str] = set()

    for tx in transactions:

        # ── Pre-check 1: negative or zero amount ─────────────────────────
        if tx.amount <= 0:
            invalid.append(
                FilteredInvalidTransaction(
                    date=tx.date,
                    amount=tx.amount,
                    message="Amount must be positive",
                )
            )
            continue

        # ── Pre-check 2: duplicate date (spec: tᵢ ≠ tⱼ) ─────────────────
        if tx.date in seen_dates:
            invalid.append(
                FilteredInvalidTransaction(
                    date=tx.date,
                    amount=tx.amount,
                    message="Duplicate transaction date",
                )
            )
            continue
        seen_dates.add(tx.date)

        # ── Step 1: ceiling and remanent ──────────────────────────────────
        ceiling = _compute_ceiling(tx.amount)
        remanent = _compute_remanent(tx.amount, ceiling)

        # ── Step 2: Q Rule (Hard Override — Latest Start Wins) ────────────
        applied_q = None
        matching_q = [q for q in q_periods if is_in_period(tx.date, q.start, q.end)]

        if matching_q:
            # If tie on start date → first in list wins (spec rule)
            winning_q = get_latest_start(matching_q)
            remanent = winning_q.fixed  # completely replaces remanent
            applied_q = AppliedQ(fixed=winning_q.fixed)

        # ── Step 3: P Rule (Stacking Bonus — All Sum) ─────────────────────
        # Applied AFTER Q — even a Q=0 remanent can gain P bonus
        applied_p = []
        matching_p = [p for p in p_periods if is_in_period(tx.date, p.start, p.end)]

        for p in matching_p:
            remanent += p.extra
            applied_p.append(AppliedP(extra=p.extra))

        # ── Step 4: K Rule (must belong to at least one K window) ─────────
        in_k = any(is_in_period(tx.date, k.start, k.end) for k in k_periods)

        if not in_k:
            invalid.append(
                FilteredInvalidTransaction(
                    date=tx.date,
                    amount=tx.amount,
                    message="Not within any K period",
                )
            )
            continue

        valid.append(
            FilteredTransaction(
                date=tx.date,
                amount=tx.amount,
                ceiling=ceiling,
                remanent=round(remanent, 2),
                appliedQ=applied_q,
                appliedP=applied_p,
                inKPeriod=True,
            )
        )

    return valid, invalid


# ── Utility for returns calculation step ─────────────────────────────────────


def sum_remanents_for_k_period(
        transactions: List[FilteredTransaction],
        k: KPeriod,
) -> float:
    """
    Sum remanents for all valid transactions within a K period.
    A transaction can count in MULTIPLE K periods — intentional per spec.
    """
    return round(
        sum(
            tx.remanent for tx in transactions if is_in_period(tx.date, k.start, k.end)
        ),
        2,
    )
