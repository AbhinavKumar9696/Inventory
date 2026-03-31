from redis.asyncio import Redis

from app.core.exceptions import AppException
from app.models.stock_movement import MovementType, StockMovement
from app.repositories.item_repository import ItemRepository
from app.repositories.movement_repository import MovementRepository
from app.schemas.movement import StockMovementCreate
from app.tasks.inventory_tasks import send_low_stock_alert


class InventoryService:
    def __init__(
        self,
        item_repository: ItemRepository,
        movement_repository: MovementRepository,
        redis_client: Redis,
    ) -> None:
        self.item_repository = item_repository
        self.movement_repository = movement_repository
        self.redis = redis_client

    async def move_stock(self, payload: StockMovementCreate, user_id: int) -> StockMovement:
        item = await self.item_repository.get_by_id(payload.item_id)
        if not item:
            raise AppException("Inventory item not found", status_code=404)

        if payload.movement_type == MovementType.out and item.quantity < payload.quantity:
            raise AppException("Insufficient stock", status_code=400)

        if payload.movement_type == MovementType.in_:
            item.quantity += payload.quantity
        else:
            item.quantity -= payload.quantity

        movement = StockMovement(
            item_id=item.id,
            quantity=payload.quantity,
            movement_type=payload.movement_type,
            note=payload.note,
            performed_by=user_id,
        )

        await self.item_repository.update(item)
        created = await self.movement_repository.create(movement)
        await self.redis.delete("inventory:items:all", f"inventory:item:{item.id}")

        if item.quantity <= item.reorder_level:
            send_low_stock_alert.delay(item.id, item.sku, item.quantity, item.reorder_level)

        return created

    async def list_item_movements(self, item_id: int) -> list[StockMovement]:
        return await self.movement_repository.list_for_item(item_id)

