from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_movement import StockMovement


class MovementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, movement: StockMovement) -> StockMovement:
        self.session.add(movement)
        await self.session.commit()
        await self.session.refresh(movement)
        return movement

    async def list_for_item(self, item_id: int) -> list[StockMovement]:
        stmt = (
            select(StockMovement)
            .where(StockMovement.item_id == item_id)
            .order_by(StockMovement.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
