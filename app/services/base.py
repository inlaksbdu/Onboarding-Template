from abc import ABC, abstractmethod
from typing import Any, Dict
import httpx
from app.core.logger import get_logger
from app.core.exceptions import BaseCustomException

logger = get_logger(name)

class BaseService(ABC):
    def init(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = get_logger(self.class.name)

    async def aenter(self):
        return self

    async def aexit(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service-specific requirements"""
        pass

    async def make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        **kwargs
    ) -> Any:
        """Make HTTP request with error handling and logging"""
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error occurred: {str(e)}")
            raise BaseCustomException(
                status_code=response.status_code if response else 500,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise
