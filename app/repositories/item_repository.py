from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_item import InventoryItem


class ItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, item_id: int) -> InventoryItem | None:
        result = await self.session.execute(
            select(InventoryItem).where(InventoryItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> InventoryItem | None:
        result = await self.session.execute(select(InventoryItem).where(InventoryItem.sku == sku))
        return result.scalar_one_or_none()

    async def list_items(self, *, offset: int, limit: int) -> list[InventoryItem]:
        result = await self.session.execute(
            select(InventoryItem).order_by(InventoryItem.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_items(self) -> int:
        result = await self.session.execute(select(func.count(InventoryItem.id)))
        return result.scalar_one()

    async def get_total_quantity(self) -> int:
        result = await self.session.execute(
            select(func.sum(InventoryItem.quantity))
        )
        total = result.scalar()
        return total or 0

    async def create(self, item: InventoryItem) -> InventoryItem:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def update(self, item: InventoryItem) -> InventoryItem:
        await self.session.commit()
        await self.session.refresh(item)
        return item
