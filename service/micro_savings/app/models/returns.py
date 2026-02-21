from typing import List, Optional

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
    wage: float
    inflation: float = 5.5
    q: List[QPeriod] = []
    p: List[PPeriod] = []
    k: List[KPeriod]
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
    start: str
    end: str
    amount: float
    profit: float
    taxBenefit: Optional[float] = None


class ReturnResponse(BaseModel):
    totalTransactionAmount: float
    totalCeiling: float
    savingsByDates: List[SavingsByDate]
