from fastapi import APIRouter
from service.micro_savings.app.api.endpoints.performance.performance_utils import get_performance_metrics

router = APIRouter()


@router.get("/performance")
def performance():
    """
    System health check — returns live server metrics.

    No input required.

    Returns:
        time    → uptime since server started  (HH:MM:SS.mmm)
        memory  → current RAM usage            (e.g. "25.11 MB")
        threads → number of active threads     (int)
    """
    return get_performance_metrics()
