from typing import List

from pydantic import BaseModel

from service.micro_savings.app.models.periods import (
    QPeriod,
    PPeriod,
    KPeriod,
)
from service.micro_savings.app.models.transaction import ValidatedTransaction


class FilterRequest(BaseModel):
    wage: float
    q: List[QPeriod] = []
    p: List[PPeriod] = []
    k: List[KPeriod]
    transactions: List[ValidatedTransaction]
