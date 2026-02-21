from fastapi import APIRouter

from service.micro_savings.app.models.returns import ReturnResponse, ReturnRequest
from service.micro_savings.app.transaction_engine.returns_processor import (
    compute_nps_returns,
    compute_index_returns,
)

router = APIRouter()


@router.post("/returns:nps", response_model=ReturnResponse)
def nps_returns(request: ReturnRequest):
    """
    Calculate retirement corpus via NPS (National Pension Scheme).

    Rate of return: 7.11% annually
    Investment horizon: max(60 - age, 5) years

    NPS-specific benefit:
        Tax deduction = min(invested, 10% of annual_wage, ₹2,00,000)
        taxBenefit    = tax(annual_wage) − tax(annual_wage − deduction)

    Per K period output:
        amount     → total remanent saved in this window
        profit     → nominal profit at retirement (FV - principal)
        taxBenefit → INR saved in taxes due to NPS deduction
    """
    return compute_nps_returns(
        transactions=request.transactions,
        k_periods=request.k,
        age=request.age,
        wage=request.wage,
        inflation=request.inflation,
    )


@router.post("/returns:index", response_model=ReturnResponse)
def index_returns(request: ReturnRequest):
    """
    Calculate retirement corpus via Index Fund investment.

    Rate of return: 14.49% annually (higher risk, higher reward)
    Investment horizon: max(60 - age, 5) years

    No tax benefit applies for index funds.

    Per K period output:
        amount     → total remanent saved in this window
        profit     → nominal profit at retirement (FV - principal)
        taxBenefit → always 0.0 (index funds have no 80CCD benefit)
    """
    return compute_index_returns(
        transactions=request.transactions,
        k_periods=request.k,
        age=request.age,
        wage=request.wage,
        inflation=request.inflation,
    )
