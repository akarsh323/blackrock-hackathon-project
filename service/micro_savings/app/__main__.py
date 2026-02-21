import uvicorn

from service.micro_savings.app.utils.settings import settings


def main():
    uvicorn.run(
        "service.micro_savings.app.api.application:get_app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers,
        log_level="info",
        factory=True,
    )


if __name__ == "__main__":
    main()
