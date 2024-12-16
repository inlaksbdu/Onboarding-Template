from bootstrap.container import Container
from customer.api.customer_route import router as customer_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

import uvicorn
import os
import sys


def create_app() -> FastAPI:
    container = Container()

    app = FastAPI(
        title="Customer Onboarding API",
        version="1.0.0",
    )

    logger.info("Configuring CORS...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Wire the container with correct module path
    logger.info("Wiring dependency container...")
    container.wire(
        modules=[
            "customer.api.customer_route"  # Updated path
        ]
    )

    # Include routers
    logger.info("Including API routers...")
    app.include_router(customer_router)

    # Store container reference
    app.container = container

    logger.info("Application startup complete!")
    return app


app = create_app()


@app.on_event("startup")
async def startup():
    logger.info("Running application startup tasks...")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Running application shutdown tasks...")


# Main execution
if __name__ == "__main__":
    uvicorn_config = {
        "app": "main:app",
        "host": "127.0.0.1",
        "port": 8000,
        "log_level": "debug",
        "loop": "asyncio",
    }

    if os.getenv("APP_ENV") == "production":
        uvicorn_config["reload"] = True

    uvicorn.run(**uvicorn_config)
