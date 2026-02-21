from typing import List

from pydantic import BaseModel

from service.micro_savings.app.models.transaction import ParsedTransaction


class ValidatorRequest(BaseModel):
    wage: float
    transactions: List[ParsedTransaction]
