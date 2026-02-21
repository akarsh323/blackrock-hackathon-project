from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from service.micro_savings.app.api.endpoints.transaction.transaction import ValidatedTransaction, FilterResult
from service.micro_savings.app.api.endpoints.periods.periods import QPeriod, PPeriod, KPeriod
from service.micro_savings.app.api.endpoints.qpk.qpk_service import apply_qpk

router = APIRouter()


class FilterRequest(BaseModel):
    wage: float
    q: List[QPeriod] = []
    p: List[PPeriod] = []
    k: List[KPeriod]
    transactions: List[ValidatedTransaction]


@router.post("/transactions:filter", response_model=FilterResult)
def filter_transactions(request: FilterRequest):
    """
    Step 3 — Apply Q, P, K period rules to each transaction.

    Q Rule (Hard Override — Latest Wins):
        If multiple Q periods match a date, use the one with the LATEST start.
        That Q's fixed value completely replaces the calculated remanent.

    P Rule (Stacking Bonus — All Sum):
        ALL matching P periods add their extra to the remanent.
        Applied AFTER Q (so even a Q=0 remanent can receive P bonus).

    K Rule (Reporting Windows):
        Transactions are grouped per K period for reporting.
        A single transaction can appear in MULTIPLE K periods.
        Transactions outside all K periods → moved to invalid.

    Returns:
        valid   → transactions with updated remanents and K membership
        invalid → transactions outside all K periods
    """
    valid, invalid = apply_qpk(
        request.transactions,
        request.q,
        request.p,
        request.k,
    )
    return FilterResult(valid=valid, invalid=invalid)
