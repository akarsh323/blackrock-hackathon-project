from datetime import datetime
from typing import Optional

DATE_FMT = "%Y-%m-%d %H:%M:%S"


def parse_dt(date_str: str) -> datetime:
    """Convert a date string into a datetime object."""
    return datetime.strptime(date_str, DATE_FMT)


def format_dt(dt: datetime) -> str:
    """Convert a datetime object back to the standard string format."""
    return dt.strftime(DATE_FMT)


def is_in_period(date_str: str, start_str: str, end_str: str) -> bool:
    """
    Check if a date falls within a period (inclusive on both ends).

    Example:
        is_in_period("2023-07-15 14:00:00", "2023-07-01 00:00:00", "2023-07-31 23:59:59")
        → True
    """
    date  = parse_dt(date_str)
    start = parse_dt(start_str)
    end   = parse_dt(end_str)
    return start <= date <= end


def periods_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    """
    Check if two date periods overlap at all.

    Example:
        periods_overlap("2023-01-01", "2023-06-30", "2023-04-01", "2023-12-31")
        → True  (April–June overlaps)
    """
    s1, e1 = parse_dt(start1), parse_dt(end1)
    s2, e2 = parse_dt(start2), parse_dt(end2)
    return s1 <= e2 and s2 <= e1


def years_between(date_str: str, reference_str: str) -> float:
    """
    Calculate decimal years between two date strings.
    Used internally for time-weighted calculations.
    """
    d1 = parse_dt(date_str)
    d2 = parse_dt(reference_str)
    delta = abs((d2 - d1).days)
    return delta / 365.25


def get_latest_start(periods: list) -> Optional[object]:
    """
    From a list of period objects (with .start attribute),
    return the one with the LATEST start date.
    Used for Q period conflict resolution.

    Example:
        Q1 starts Jan → Q2 starts Mar → Q2 wins
    """
    if not periods:
        return None
    return max(periods, key=lambda p: parse_dt(p.start))
