from typing import Any

from fastapi import HTTPException
from loguru import logger
from pydantic import ValidationError

EXCEPTION_MAP: dict[type[BaseException], dict[str, Any]] = {
    # ── Validation / Input errors ──────────────────────────────────────────
    ValidationError: {
        "status_code": 422,
        "message": "Request body failed schema validation.",
    },
    ValueError: {
        "status_code": 400,
        "message": "Invalid value supplied in the request.",
    },
    TypeError: {
        "status_code": 400,
        "message": "Incorrect type supplied in the request.",
    },
    KeyError: {
        "status_code": 400,
        "message": "A required field is missing from the request.",
    },
    # ── Business-logic errors ──────────────────────────────────────────────
    ZeroDivisionError: {
        "status_code": 400,
        "message": "A division-by-zero occurred during calculation.",
    },
    OverflowError: {
        "status_code": 400,
        "message": "A numeric overflow occurred during calculation.",
    },
    ArithmeticError: {
        "status_code": 400,
        "message": "An arithmetic error occurred during processing.",
    },
    # ── Runtime / unexpected errors ────────────────────────────────────────
    NotImplementedError: {
        "status_code": 501,
        "message": "This feature is not yet implemented.",
    },
    RuntimeError: {
        "status_code": 500,
        "message": "An unexpected runtime error occurred.",
    },
    Exception: {
        "status_code": 500,
        "message": "An unexpected internal server error occurred.",
    },
}


def handle_exception(exc: BaseException) -> None:
    """
    Resolve an exception against EXCEPTION_MAP and raise an HTTPException.

    This function must be called inside the except block of every endpoint.
    It looks up the exception type (walking the MRO for the closest match),
    retrieves the mapped status_code and message, appends the live exception
    detail, logs the error, and raises an HTTPException for FastAPI to return.

    Args:
        exc: The caught exception instance.

    Usage in an endpoint::

        @router.post("/some-path")
        def my_endpoint(request: MyRequest):
            try:
                return do_something(request)
            except Exception as exc:
                handle_exception(exc)

    Raises:
        HTTPException: always — never returns normally.
    """
    mapping = EXCEPTION_MAP.get(type(exc), EXCEPTION_MAP[Exception])
    status_code: int = mapping["status_code"]
    default_msg: str = mapping["message"]

    live_msg = str(exc).strip()
    detail = f"{default_msg} Detail: {live_msg}" if live_msg else default_msg

    logger.error(
        "Exception [{cls}] → HTTP {code}: {detail}",
        cls=type(exc).__name__,
        code=status_code,
        detail=detail,
    )
    raise HTTPException(status_code=status_code, detail=detail)
