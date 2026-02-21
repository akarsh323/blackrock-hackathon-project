from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifespan for startup and shutdown events.

    This async context manager is executed once when the application starts
    and once when it shuts down. All code before ``yield`` runs at startup;
    all code after ``yield`` runs at shutdown.

    Use this to initialise shared resources (database pools, HTTP clients,
    caches, background task schedulers, etc.) and attach them to
    ``app.state`` so they are accessible across the entire request lifecycle.
    Clean up and release those resources in the block after ``yield``.

    Args:
        app: The FastAPI application instance. Resources are attached to
             ``app.state`` so they can be accessed from route handlers via
             ``request.app.state``.

    Yields:
        None — control is yielded back to the ASGI server to begin serving
        requests after startup is complete.

    Example::

        async with lifespan(app):
            # startup has run, app is serving requests
            ...
        # shutdown has run here
    """

    logger.info("Starting lifespan")

    app.state.db_connection = None

    yield

    logger.info("Ending lifespan")
