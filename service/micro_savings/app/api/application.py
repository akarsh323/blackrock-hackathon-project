from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from service.micro_savings.app.api.endpoints.router import router
from service.micro_savings.app.api.lifespan import lifespan
from service.micro_savings.app.utils.logging import setup_logging


def get_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="micro_savings",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # replace with explicit origins in prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router=router, prefix="/api")

    return app
