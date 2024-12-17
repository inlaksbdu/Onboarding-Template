from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.id_card import IdCardData


class OnboardingUtils:
    @staticmethod
    async def get_id_card_data_by_id(db: AsyncSession, id: Any) -> IdCardData | None:
        return await db.get(IdCardData, id)

    @staticmethod
    async def get_id_card_data_by_user_id(
        db: AsyncSession, user_id: Any
    ) -> IdCardData | None:
        return (
            (await db.execute(select(IdCardData).where(IdCardData.user_id == user_id)))
            .scalars()
            .first()
        )

    @staticmethod
    async def get_id_card_data_by_id_card_number(
        db: AsyncSession, id_card_number: str
    ) -> IdCardData | None:
        return (
            (
                await db.execute(
                    select(IdCardData).where(IdCardData.id_number == id_card_number)
                )
            )
            .scalars()
            .first()
        )

    @staticmethod
    async def add_id_card_data(
        db: AsyncSession, id_card_data: IdCardData
    ) -> IdCardData:
        db.add(id_card_data)
        await db.commit()
        await db.refresh(id_card_data)
        return id_card_data
