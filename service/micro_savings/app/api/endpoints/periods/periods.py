from pydantic import BaseModel, validator
from datetime import datetime


DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _parse_dt(v: str) -> str:
    try:
        datetime.strptime(v, DATE_FMT)
    except ValueError:
        raise ValueError(f"Date '{v}' must be in format YYYY-MM-DD HH:MM:SS")
    return v


class QPeriod(BaseModel):
    """
    Q Period — Hard override.
    Replaces the calculated remanent with a fixed amount.
    When multiple Q periods overlap, the one with the LATEST start date wins.
    """
    fixed: float        # The fixed remanent value to substitute
    start: str          # Period start datetime string
    end: str            # Period end datetime string

    @validator("start", "end")
    def validate_dates(cls, v):
        return _parse_dt(v)


class PPeriod(BaseModel):
    """
    P Period — Stacking bonus.
    Adds extra amount on top of remanent (after Q is applied).
    ALL overlapping P periods are summed together.
    """
    extra: float        # Extra amount to add to remanent
    start: str
    end: str

    @validator("start", "end")
    def validate_dates(cls, v):
        return _parse_dt(v)


class KPeriod(BaseModel):
    """
    K Period — Reporting window.
    Transactions are grouped and summed per K period.
    A single transaction can belong to multiple K periods.
    """
    start: str
    end: str

    @validator("start", "end")
    def validate_dates(cls, v):
        return _parse_dt(v)
