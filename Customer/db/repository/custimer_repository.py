from typing import Optional, List
from sqlalchemy import select, update, delete
from fastapi import HTTPException
from loguru import logger

from persistence.db.models.base import SessionLocal
from persistence.db.models.customer import Customer
from Customer.dto.requests.customer_request import CustomerCreateRequest, CustomerUpdateRequest

class CustomerRepository:
    """
    Repository class for handling data access for Customer entities.
    """

    def __init__(self):
        # The repository uses dependency injection of the database session
        pass

    async def create_customer(self, customer: Customer) -> Customer:
        """
        Create a new customer in the database.
        """
        try:
            async with SessionLocal() as session:
                session.add(customer)
                await session.commit()
                await session.refresh(customer)
                return customer
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """
        Retrieve a customer by their ID.
        """
        try:
            async with SessionLocal() as session:
                statement = select(Customer).where(Customer.id == customer_id)
                result = await session.execute(statement)
                return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting customer by ID: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_all_customers(self) -> List[Customer]:
        """
        Retrieve all customers from the database.
        """
        try:
            async with SessionLocal() as session:
                statement = select(Customer)
                result = await session.execute(statement)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all customers: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_customer(self, customer_id: int, customer_data: dict) -> Optional[Customer]:
        """
        Update an existing customer in the database.
        """
        try:
            async with SessionLocal() as session:
                statement = (
                    update(Customer)
                    .where(Customer.id == customer_id)
                    .values(**customer_data)
                    .returning(Customer)
                )
                result = await session.execute(statement)
                await session.commit()
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error updating customer: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_customer(self, customer_id: int) -> bool:
        """
        Delete a customer from the database.
        """
        try:
            async with SessionLocal() as session:
                statement = delete(Customer).where(Customer.id == customer_id)
                result = await session.execute(statement)
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting customer: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))