from typing import List

from fastapi import APIRouter

from service.micro_savings.app.models.transaction import (
    RawTransaction,
    ParsedTransaction,
)
from service.micro_savings.app.transaction_engine.ceiling_processor.ceiling_service import (
    parse_all,
)

router = APIRouter()


@router.post("/transactions:parse", response_model=List[ParsedTransaction])
def parse_transactions(transactions: List[RawTransaction]):
    """
    Step 1 — Enrich raw transactions with ceiling and remanent.

    For each transaction:
        ceiling  = ceil(amount / 100) * 100
        remanent = ceiling - amount   ← this is what gets invested

    Example:
        amount=250  →  ceiling=300,  remanent=50
        amount=300  →  ceiling=300,  remanent=0   (exact multiple)
        amount=847  →  ceiling=900,  remanent=53
    """
    return parse_all(transactions)
