from typing import List

from pydantic import BaseModel, validator

from service.micro_savings.app.models.periods import QPeriod, PPeriod, KPeriod
from service.micro_savings.app.models.transaction import RawTransaction


class ReturnRequest(BaseModel):
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
            raise ValueError("Age must be < 60 (retirement age is 60)")
        if v < 18:
            raise ValueError("Age must be >= 18")
        return v

    @validator("wage")
    def validate_wage(cls, v):
        if v <= 0:
            raise ValueError("Wage must be > 0")
        return v


class SavingsByDate(BaseModel):
    start: str
    end: str
    amount: float
    profit: float
    taxBenefit: float  # explicitly required, 0.0 for index


class ReturnResponse(BaseModel):
    totalTransactionAmount: float
    totalCeiling: float
    savingsByDates: List[SavingsByDate]
