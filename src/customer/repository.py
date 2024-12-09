from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from .models import Customer
from .schemas import CustomerCreate, CustomerUpdate

class CustomerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create(self, customer_data: CustomerCreate) -> Customer:
        customer = Customer(**customer_data.dict())
        self.session.add(customer)
        await self.session.commit()
        await self.session.refresh(customer)
        return customer
        
    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        query = select(Customer).where(Customer.id == customer_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_all(self) -> List[Customer]:
        query = select(Customer)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def update(self, customer_id: int, customer_data: CustomerUpdate) -> Optional[Customer]:
        update_data = customer_data.dict(exclude_unset=True)
        query = (
            update(Customer)
            .where(Customer.id == customer_id)
            .values(**update_data)
            .returning(Customer)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()
        
    async def delete(self, customer_id: int) -> bool:
        query = delete(Customer).where(Customer.id == customer_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0 