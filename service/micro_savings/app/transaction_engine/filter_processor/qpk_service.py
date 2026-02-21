import math
from typing import List, Tuple, Optional

from service.micro_savings.app.models.periods import QPeriod, PPeriod, KPeriod
from service.micro_savings.app.models.transaction import (
    RawTransaction,
    FilteredTransaction,
    FilteredInvalidTransaction,
    AppliedQ,
    AppliedP,
)
from service.micro_savings.app.utils.date_utils import is_in_period, parse_dt

# ── Step 1: Parse ─────────────────────────────────────────────────────────────


def _compute_ceiling(amount: float) -> float:
    """Round amount UP to the nearest multiple of 100."""
    return math.ceil(amount / 100) * 100


def _compute_remanent(amount: float, ceiling: float) -> float:
    return round(ceiling - amount, 2)


# ── Step 2: Validate ──────────────────────────────────────────────────────────


def _validate_transactions(
    raw: List[RawTransaction],
) -> Tuple[List[RawTransaction], List[FilteredInvalidTransaction]]:
    """
    Remove transactions that cannot participate in savings.

    Rules (checked in order, first match wins):
        1. Amount must be >= 0
        2. No duplicate timestamps (both copies are rejected)
        3. Amount must be < 500,000

    Returns:
        (valid_raw, invalid_results)
    """
    # Count occurrences of each timestamp to detect duplicates
    date_counts: dict[str, int] = {}
    for tx in raw:
        date_counts[tx.date] = date_counts.get(tx.date, 0) + 1

    valid: List[RawTransaction] = []
    invalid: List[FilteredInvalidTransaction] = []

    for tx in raw:
        if tx.amount < 0:
            invalid.append(
                FilteredInvalidTransaction(
                    date=tx.date,
                    amount=tx.amount,
                    message="Negative amounts are not allowed",
                )
            )
        elif date_counts[tx.date] > 1:
            invalid.append(
                FilteredInvalidTransaction(
                    date=tx.date,
                    amount=tx.amount,
                    message="Duplicate transaction",
                )
            )
        elif tx.amount >= 500_000:
            invalid.append(
                FilteredInvalidTransaction(
                    date=tx.date,
                    amount=tx.amount,
                    message="Amount exceeds the 500,000 limit",
                )
            )
        else:
            valid.append(tx)

    return valid, invalid


# ── Step 3a: Q rule ───────────────────────────────────────────────────────────


def _apply_q_rule(
    date: str,
    base_remanent: float,
    q_periods: List[QPeriod],
) -> Tuple[float, Optional[AppliedQ]]:
    """
    Hard override: if ANY Q period contains this date, replace remanent
    with that Q period's fixed amount.

    Conflict resolution: when multiple Q periods match, the one whose
    start date is LATEST wins.  Ties (same start) → first in the list wins.

    Returns:
        (updated_remanent, AppliedQ | None)
    """
    matching = [q for q in q_periods if is_in_period(date, q.start, q.end)]
    if not matching:
        return base_remanent, None

    # Sort: primary = latest start (desc), secondary = original list order (preserved
    # because Python sort is stable — we reverse only on the datetime key).
    winning = max(matching, key=lambda q: parse_dt(q.start))
    return winning.fixed, AppliedQ(fixed=winning.fixed)


# ── Step 3b: P rule ───────────────────────────────────────────────────────────


def _apply_p_rule(
    date: str,
    base_remanent: float,
    p_periods: List[PPeriod],
) -> Tuple[float, List[AppliedP]]:
    """
    Stacking bonus: ALL P periods that contain this date add their extra
    to the remanent.  Applied AFTER Q so even a Q=0 remanent receives P.

    Returns:
        (updated_remanent, [AppliedP, ...])
    """
    applied: List[AppliedP] = []
    for p in p_periods:
        if is_in_period(date, p.start, p.end):
            base_remanent += p.extra
            applied.append(AppliedP(extra=p.extra))
    return base_remanent, applied


# ── Step 3c: K membership ─────────────────────────────────────────────────────


def _in_any_k_period(date: str, k_periods: List[KPeriod]) -> bool:
    """True if the date falls within at least one K reporting window."""
    return any(is_in_period(date, k.start, k.end) for k in k_periods)


# ── Orchestrator ──────────────────────────────────────────────────────────────


def apply_qpk(
    raw_transactions: List[RawTransaction],
    q_periods: List[QPeriod],
    p_periods: List[PPeriod],
    k_periods: List[KPeriod],
) -> Tuple[List[FilteredTransaction], List[FilteredInvalidTransaction]]:
    """
    Full filter pipeline for a list of raw transactions.

    Processing order:
        1. Validate  — reject negatives, duplicates, over-limit amounts
        2. Parse     — compute ceiling + remanent for survivors
        3. Q rule    — override remanent with fixed amount (latest-start wins)
        4. P rule    — add extras from all matching P periods
        5. K check   — transactions outside all K windows → invalid

    Args:
        raw_transactions : list of {date, amount} expenses
        q_periods        : fixed-override periods
        p_periods        : extra-bonus periods
        k_periods        : reporting windows

    Returns:
        (valid_filtered, invalid_list)
    """
    valid_out: List[FilteredTransaction] = []
    invalid_out: List[FilteredInvalidTransaction] = []

    # ── 1. Validate ───────────────────────────────────────────────────────────
    valid_raw, validation_invalids = _validate_transactions(raw_transactions)
    invalid_out.extend(validation_invalids)

    # ── 2–5. Parse + Q/P/K per surviving transaction ──────────────────────────
    for tx in valid_raw:
        ceiling = _compute_ceiling(tx.amount)
        remanent = _compute_remanent(tx.amount, ceiling)

        # 3. Q rule
        remanent, applied_q = _apply_q_rule(tx.date, remanent, q_periods)

        # 4. P rule
        remanent, applied_p = _apply_p_rule(tx.date, remanent, p_periods)

        remanent = round(remanent, 2)

        # 5. K check
        if not _in_any_k_period(tx.date, k_periods):
            invalid_out.append(
                FilteredInvalidTransaction(
                    date=tx.date,
                    amount=tx.amount,
                    message="Transaction date is not within any K period",
                )
            )
            continue

        valid_out.append(
            FilteredTransaction(
                date=tx.date,
                amount=tx.amount,
                ceiling=ceiling,
                remanent=remanent,
                appliedQ=applied_q,
                appliedP=applied_p,
                inKPeriod=True,
            )
        )

    return valid_out, invalid_out


# ── Aggregation helper (used by returns processor) ────────────────────────────


def sum_remanents_for_k_period(
    transactions: List[FilteredTransaction],
    k: KPeriod,
) -> float:
    """
    Sum the remanents of all transactions whose date falls within a K period.

    A transaction can be counted in MULTIPLE K periods — each K period
    calculates its own independent sum.
    """
    total = sum(
        tx.remanent for tx in transactions if is_in_period(tx.date, k.start, k.end)
    )
    return round(total, 2)
