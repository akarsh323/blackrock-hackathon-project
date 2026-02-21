import math

from service.micro_savings.app.api.endpoints.transaction.transaction import (
    RawTransaction,
    ParsedTransaction,
)


def compute_ceiling(amount: float) -> float:
    """
    Round amount UP to the nearest 100.

    Examples:
        250   → 300
        300   → 300  (exact multiple, no change)
        847   → 900
        100.5 → 200
    """
    return math.ceil(amount / 100) * 100


def compute_remanent(amount: float, ceiling: float) -> float:
    """
    Remanent = the amount that gets invested.
    It's the difference between what you'd pay at ceiling vs what you spent.

    Examples:
        amount=250, ceiling=300 → remanent=50
        amount=300, ceiling=300 → remanent=0  (nothing to invest)
    """
    return round(ceiling - amount, 2)


# Test


def parse_single(tx: RawTransaction) -> ParsedTransaction:
    """
    Enrich a single raw transaction with ceiling + remanent.
    """
    ceiling = compute_ceiling(tx.amount)
    remanent = compute_remanent(tx.amount, ceiling)
    return ParsedTransaction(
        date=tx.date,
        amount=tx.amount,
        ceiling=ceiling,
        remanent=remanent,
    )


def parse_all(transactions: list[RawTransaction]) -> list[ParsedTransaction]:
    """
    Enrich a list of raw transactions. Processes each independently.
    Order is preserved.
    """
    return [parse_single(tx) for tx in transactions]
