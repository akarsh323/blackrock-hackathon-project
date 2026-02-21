from fastapi import APIRouter

from service.micro_savings.app.api.endpoints import (
    savings,
    monitoring,
    parse,
    filter,
    returns,
    performance,
    validation,
)

router = APIRouter()
router.include_router(monitoring.router, tags=["monitoring"])
router.include_router(savings.router, tags=["savings"])
router.include_router(parse.router, tags=["parse"])
router.include_router(filter.router, tags=["filter"])
router.include_router(returns.router, tags=["returns"])
router.include_router(performance.router, tags=["performance"])
router.include_router(validation.router, tags=["validation"])
