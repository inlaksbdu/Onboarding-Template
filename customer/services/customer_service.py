from loguru import logger
from fastapi import HTTPException
from typing import List

from customer.db.repository.custimer_repository import CustomerRepository
from persistence.db.models.customer import Customer
from customer.dto.requests.customer_request import (
    CustomerCreateRequest,
    CustomerUpdateRequest,
)
from customer.dto.response.customer_response import CustomerResponse


class CustomerService:
    """
    Service class for handling business logic related to Customer entities.
    """

    def __init__(
        self,
        customer_repository: CustomerRepository,
    ):
        self.customer_repository = customer_repository

    async def create_customer(
        self, customer_data: CustomerCreateRequest
    ) -> CustomerResponse:
        """
        Create a new customer.
        """
        try:
            new_customer = Customer(**customer_data.dict())
            created_customer = await self.customer_repository.create_customer(
                new_customer
            )
            return CustomerResponse.from_orm(created_customer)
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_customer(self, customer_id: int) -> CustomerResponse:
        """
        Get a customer by ID.
        """
        try:
            customer = await self.customer_repository.get_customer_by_id(customer_id)
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            return CustomerResponse.from_orm(customer)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error getting customer: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_all_customers(self) -> List[CustomerResponse]:
        """
        Get all customers.
        """
        try:
            customers = await self.customer_repository.get_all_customers()
            return [CustomerResponse.from_orm(customer) for customer in customers]
        except Exception as e:
            logger.error(f"Error getting all customers: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_customer(
        self, customer_id: int, customer_data: CustomerUpdateRequest
    ) -> CustomerResponse:
        """
        Update an existing customer.
        """
        try:
            update_data = customer_data.dict(exclude_unset=True)
            updated_customer = await self.customer_repository.update_customer(
                customer_id, update_data
            )
            if not updated_customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            return CustomerResponse.from_orm(updated_customer)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error updating customer: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_customer(self, customer_id: int) -> bool:
        """
        Delete a customer.
        """
        try:
            deleted = await self.customer_repository.delete_customer(customer_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Customer not found")
            return True
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error deleting customer: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
