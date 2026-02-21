from typing import List

from pydantic import BaseModel, validator

from service.micro_savings.app.models.periods import (
    QPeriod,
    PPeriod,
    KPeriod,
)
from service.micro_savings.app.models.transaction import RawTransaction


class ReturnRequest(BaseModel):
    """
    Full input required to calculate retirement returns.

    Accepts raw transactions (date + amount only) because the returns
    endpoint owns the complete pipeline:
        parse → validate → apply Q/P/K → compute returns per K period

    All period rules (q, p, k) are applied internally; callers do not
    need to pre-process transactions.
    """

    age: int
    wage: float  # Monthly wage in INR
    inflation: float = (
        5.5  # Annual inflation rate as a plain percentage (e.g. 5.5 means 5.5%)
    )
    q: List[QPeriod] = []
    p: List[PPeriod] = []
    k: List[KPeriod]  # At least one K period required for grouping
    transactions: List[RawTransaction]

    @validator("age")
    def validate_age(cls, v):
        if v >= 60:
            raise ValueError("Age must be less than 60 (retirement age is 60)")
        if v < 18:
            raise ValueError("Age must be at least 18")
        return v

    @validator("wage")
    def validate_wage(cls, v):
        if v <= 0:
            raise ValueError("Wage must be positive")
        return v


class SavingsByDate(BaseModel):
    """Savings summary and projected returns for a single K period."""

    start: str  # K period start timestamp
    end: str  # K period end timestamp
    amount: float  # Total remanent saved within this K period
    profit: float  # Inflation-adjusted profit at retirement (real_fv - principal)
    taxBenefit: float  # Tax saved via NPS deduction (always 0.0 for Index Fund)


class ReturnResponse(BaseModel):
    """Full return calculation response."""

    totalTransactionAmount: float  # Sum of valid raw expense amounts
    totalCeiling: float  # Sum of ceiling values for valid transactions
    savingsByDates: List[SavingsByDate]
