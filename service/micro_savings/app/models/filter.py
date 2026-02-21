from datetime import datetime
from typing import List

from pydantic import BaseModel, validator

from service.micro_savings.app.models.periods import QPeriod, PPeriod, KPeriod


class FilterInputTransaction(BaseModel):
    """
    Transaction as received by the filter endpoint.
    Only date + amount — ceiling and remanent are computed
    internally by this endpoint (spec Step 1).
    """

    date: str
    amount: float

    @validator("date")
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(f"Date '{v}' must be in format YYYY-MM-DD HH:MM:SS")
        return v


class FilterRequest(BaseModel):
    wage: float
    q: List[QPeriod] = []
    p: List[PPeriod] = []
    k: List[KPeriod]  # required — no default
    transactions: List[FilterInputTransaction]
