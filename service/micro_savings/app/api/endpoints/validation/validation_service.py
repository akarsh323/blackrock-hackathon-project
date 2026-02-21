from typing import List, Tuple
from service.micro_savings.app.api.endpoints.transaction.transaction import ParsedTransaction, ValidatedTransaction, InvalidTransaction
from service.micro_savings.app.api.endpoints.ceiling.ceiling_service import compute_ceiling


def validate_transactions(
    transactions: List[ParsedTransaction],
    wage: float
) -> Tuple[List[ValidatedTransaction], List[InvalidTransaction]]:
    """
    Run all validation rules against a list of parsed transactions.

    Rules (in order):
        1. Amount must be non-negative
        2. No duplicate timestamps
        3. Amount must be < 500,000
        4. Ceiling value must match recomputed ceil(amount/100)*100

    Returns:
        (valid_list, invalid_list)
    """
    valid:   List[ValidatedTransaction] = []
    invalid: List[InvalidTransaction]   = []

    # Pre-scan: collect all dates to detect duplicates
    seen_dates = {}
    for tx in transactions:
        seen_dates[tx.date] = seen_dates.get(tx.date, 0) + 1

    already_flagged_dates = set()

    for tx in transactions:
        reason = _check(tx, seen_dates, already_flagged_dates)

        if reason:
            invalid.append(InvalidTransaction(
                date=tx.date,
                amount=tx.amount,
                message=reason
            ))
            # Mark date as flagged so the duplicate pair is also caught
            if seen_dates.get(tx.date, 0) > 1:
                already_flagged_dates.add(tx.date)
        else:
            valid.append(ValidatedTransaction(
                date=tx.date,
                amount=tx.amount,
                ceiling=tx.ceiling,
                remanent=tx.remanent,
            ))

    return valid, invalid


def _check(tx: ParsedTransaction, seen_dates: dict, already_flagged: set) -> str | None:
    """
    Returns a failure reason string if invalid, else None.
    Checks are ordered: first match short-circuits.
    """

    # Rule 1: Negative amount
    if tx.amount < 0:
        return "Amount cannot be negative"

    # Rule 2: Duplicate timestamp
    if seen_dates.get(tx.date, 0) > 1:
        return "Duplicate timestamp detected"

    # Rule 3: Exceeds maximum allowed transaction
    if tx.amount >= 500_000:
        return "Amount exceeds 500,000 limit"

    # Rule 4: Ceiling mismatch (data integrity check)
    expected_ceiling = compute_ceiling(tx.amount)
    if abs(tx.ceiling - expected_ceiling) > 0.01:
        return f"Ceiling mismatch: expected {expected_ceiling}, got {tx.ceiling}"

    return None
