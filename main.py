# from bootstrap.container import Container
# from customer.api.customer_route import router as customer_router
from auth.api import router as auth_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

import uvicorn
import os
import sys


class App(FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.container = Container()
        # self.container.wire(modules=["customer.api.customer_route"])
        # self.include_router(customer_router)
        self.include_router(auth_router)

        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


app = App(title="Onboarding API", version="0.1.0")


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
