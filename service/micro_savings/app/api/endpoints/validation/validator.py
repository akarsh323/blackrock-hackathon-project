from fastapi import APIRouter

from service.micro_savings.app.models.transaction import (
    ValidationResult,
)
from service.micro_savings.app.models.validator import ValidatorRequest
from service.micro_savings.app.transaction_engine.validation_processor.validation_service import (
    validate_transactions,
)

router = APIRouter()


@router.post("/transactions:validator", response_model=ValidationResult)
def validate(request: ValidatorRequest):
    """
    Step 2 — Remove bad transactions before they enter the savings calculation.

    Validation rules:
        ✗  Negative amounts
        ✗  Duplicate timestamps (same second = same transaction)
        ✗  Amounts >= 500,000 (problem constraint)
        ✗  Ceiling values that don't match ceil(amount/100)*100

    Returns:
        valid   → transactions that passed all checks
        invalid → transactions that failed, with the reason
    """
    valid, invalid = validate_transactions(request.transactions, request.wage)
    return ValidationResult(valid=valid, invalid=invalid)
