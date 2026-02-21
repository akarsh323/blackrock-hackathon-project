from fastapi import APIRouter

from service.micro_savings.app.models.returns import ReturnResponse, ReturnRequest
from service.micro_savings.app.transaction_engine.returns_processor.returns_service import (
    compute_nps_returns,
    compute_index_returns,
)

router = APIRouter()


@router.post("/returns:nps", response_model=ReturnResponse)
def nps_returns(request: ReturnRequest):
    """
    Calculate retirement corpus via NPS (National Pension Scheme).

    Full pipeline (no pre-processing required from the caller):
        parse → validate → Q/P/K rules → compound interest → inflation adjustment

    Rate of return : 7.11% annually
    Investment horizon : max(60 - age, 5) years

    NPS tax benefit (Section 80CCD):
        deduction  = min(invested, 10% of annual_wage, ₹2,00,000)
        taxBenefit = tax(annual_wage) − tax(annual_wage − deduction)

    Per K period output:
        amount     → total remanent (savings) within this window
        profit     → inflation-adjusted profit at retirement (real_fv - principal)
        taxBenefit → INR saved in taxes via NPS deduction
    """
    return compute_nps_returns(
        transactions=request.transactions,
        k_periods=request.k,
        q_periods=request.q,
        p_periods=request.p,
        age=request.age,
        wage=request.wage,
        inflation=request.inflation,
    )


@router.post("/returns:index", response_model=ReturnResponse)
def index_returns(request: ReturnRequest):
    """
    Calculate retirement corpus via Index Fund (e.g. NIFTY 50).

    Full pipeline (no pre-processing required from the caller):
        parse → validate → Q/P/K rules → compound interest → inflation adjustment

    Rate of return : 14.49% annually
    Investment horizon : max(60 - age, 5) years

    No tax benefit for index fund investments.

    Per K period output:
        amount     → total remanent (savings) within this window
        profit     → inflation-adjusted profit at retirement (real_fv - principal)
        taxBenefit → always 0.0
    """
    return compute_index_returns(
        transactions=request.transactions,
        k_periods=request.k,
        q_periods=request.q,
        p_periods=request.p,
        age=request.age,
        wage=request.wage,
        inflation=request.inflation,
    )
