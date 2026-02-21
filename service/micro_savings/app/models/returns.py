from typing import List

from pydantic import BaseModel, validator

from service.micro_savings.app.models.periods import (
    QPeriod,
    PPeriod,
    KPeriod,
)
from service.micro_savings.app.models.transaction import ParsedTransaction


class ReturnRequest(BaseModel):
    """
    Full input required to calculate retirement returns.
    Includes user profile, all period rules, and parsed transactions.
    """

    age: int  # Current age of investor
    wage: float  # Monthly wage in INR
    inflation: float = 5.5  # Annual inflation rate (%)
    q: List[QPeriod] = []
    p: List[PPeriod] = []
    k: List[KPeriod]  # At least one K period required
    transactions: List[ParsedTransaction]

    @validator("age")
    def validate_age(cls, v):
        if v >= 60:
            raise ValueError("Age must be less than 60 (retirement age)")
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

    start: str  # K period start
    end: str  # K period end
    amount: float  # Total remanent saved in this period
    profit: float  # Projected profit at retirement (nominal)
    taxBenefit: float  # Tax saved due to NPS deduction (NPS only)


class ReturnResponse(BaseModel):
    """Full return calculation response."""

    totalTransactionAmount: float  # Sum of all raw expense amounts
    totalCeiling: float  # Sum of all ceiling values
    savingsByDates: List[SavingsByDate]  # Per-K-period breakdown
