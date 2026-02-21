from typing import List, Tuple

from service.micro_savings.app.models.transaction import (
    ParsedTransaction,
    ValidatedTransaction,
    InvalidTransaction,
)


def validate_transactions(
    transactions: List[ParsedTransaction], wage: float
) -> Tuple[List[ValidatedTransaction], List[InvalidTransaction]]:
    """
    Run all validation rules against a list of parsed transactions.
    """
    valid: List[ValidatedTransaction] = []
    invalid: List[InvalidTransaction] = []

    seen_dates = {}
    for tx in transactions:
        seen_dates[tx.date] = seen_dates.get(tx.date, 0) + 1

    already_flagged_dates = set()

    for tx in transactions:
        reason = _check(tx, seen_dates, already_flagged_dates)

        if reason:
            invalid.append(
                InvalidTransaction(
                    date=tx.date,
                    amount=tx.amount,
                    ceiling=tx.ceiling,
                    remanent=tx.remanent,
                    message=reason,
                )
            )
            # Prevent duplicate message spam for the same date
            if seen_dates.get(tx.date, 0) > 1:
                already_flagged_dates.add(tx.date)
        else:
            valid.append(
                ValidatedTransaction(
                    date=tx.date,
                    amount=tx.amount,
                    ceiling=tx.ceiling,
                    remanent=tx.remanent,
                )
            )

    return valid, invalid


def _check(tx: ParsedTransaction, seen_dates: dict, already_flagged: set) -> str | None:
    # Rule 1: Negative amounts are explicitly forbidden in the PDF specs
    if tx.amount < 0:
        return "Negative amounts are not allowed"

    # Rule 2: Multiple transactions at the exact same second are duplicates
    if seen_dates.get(tx.date, 0) > 1:
        return "Duplicate transaction"

    # Rule 3: Amount cannot exceed constraints defined in the problem
    if tx.amount >= 500_000:
        return "Amount exceeds 500,000 limit"

    # Return None if it passes all checks
    return None
