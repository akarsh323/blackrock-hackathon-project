from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, validator


# ── Raw input ─────────────────────────────────────────────────────────────────


class RawTransaction(BaseModel):
    """A transaction exactly as received from the user."""

    date: str
    amount: float

    @validator("date")
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(f"Date '{v}' must be in format YYYY-MM-DD HH:MM:SS")
        return v


# ── Parsed (ceiling + remanent added) ─────────────────────────────────────────


class ParsedTransaction(BaseModel):
    """Transaction enriched with ceiling and remanent values."""

    date: str
    amount: float
    ceiling: float
    remanent: float


# ── After validation step ──────────────────────────────────────────────────────


class ValidatedTransaction(BaseModel):
    """Transaction that passed all validation checks."""

    date: str
    amount: float
    ceiling: float
    remanent: float


class InvalidTransaction(BaseModel):
    """Transaction that failed validation, with reason."""

    date: str
    amount: float
    ceiling: Optional[float] = None
    remanent: Optional[float] = None
    message: str


class ValidationResult(BaseModel):
    valid: List[ValidatedTransaction]
    invalid: List[InvalidTransaction]


# ── After filter step (Q/P/K applied) ─────────────────────────────────────────


class AppliedQ(BaseModel):
    fixed: float


class AppliedP(BaseModel):
    extra: float


class FilteredTransaction(BaseModel):
    """Transaction after Q/P rules applied and K period checked."""

    date: str
    amount: float
    ceiling: float
    remanent: float
    appliedQ: Optional[AppliedQ] = None
    appliedP: List[AppliedP] = []
    inKPeriod: bool


class FilteredInvalidTransaction(BaseModel):
    date: str
    amount: Optional[float] = None
    message: str


class FilterResult(BaseModel):
    valid: List[FilteredTransaction]
    invalid: List[FilteredInvalidTransaction]
