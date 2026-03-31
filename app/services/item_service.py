import json
import math

from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.models.inventory_item import InventoryItem
from app.repositories.item_repository import ItemRepository
from app.schemas.item import (
    ItemCreate,
    ItemQuantityTotalRead,
    ItemRead,
    ItemUpdate,
    PaginatedItemRead,
)


class ItemService:
    def __init__(self, item_repository: ItemRepository, redis_client: Redis) -> None:
        self.item_repository = item_repository
        self.redis = redis_client
        self.settings = get_settings()

    @staticmethod
    def _item_key(item_id: int) -> str:
        return f"inventory:item:{item_id}"

    @staticmethod
    def _items_version_key() -> str:
        return "inventory:items:version"

    @classmethod
    def _items_key(cls, page: int, page_size: int, version: str) -> str:
        return f"inventory:items:v{version}:page:{page}:size:{page_size}"

    async def list_items(self, page: int = 1, page_size: int = 20) -> PaginatedItemRead:
        version = await self.redis.get(self._items_version_key())
        version_value = version.decode() if isinstance(version, bytes) else str(version or "1")
        cache_key = self._items_key(page, page_size, version_value)
        cached = await self.redis.get(cache_key)
        if cached:
            payload = json.loads(cached)
            return PaginatedItemRead.model_validate(payload)

        offset = (page - 1) * page_size
        items = await self.item_repository.list_items(offset=offset, limit=page_size)
        total_items = await self.item_repository.count_items()
        total_pages = math.ceil(total_items / page_size) if total_items else 0
        result = PaginatedItemRead(
            items=[ItemRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )
        await self.redis.setex(
            cache_key,
            self.settings.redis_cache_ttl_seconds,
            result.model_dump_json(),
        )
        return result

    async def get_item(self, item_id: int) -> ItemRead:
        cached = await self.redis.get(self._item_key(item_id))
        if cached:
            payload = json.loads(cached)
            return ItemRead.model_validate(payload)

        item = await self.item_repository.get_by_id(item_id)
        if not item:
            raise AppException("Inventory item not found", status_code=404)

        serialized = ItemRead.model_validate(item)
        await self.redis.setex(
            self._item_key(item_id),
            self.settings.redis_cache_ttl_seconds,
            serialized.model_dump_json(),
        )
        return serialized

    async def get_total_quantity(self) -> ItemQuantityTotalRead:
        total_quantity = await self.item_repository.get_total_quantity()
        return ItemQuantityTotalRead(total_quantity=total_quantity)

    async def get_item_model_or_404(self, item_id: int) -> InventoryItem:
        item = await self.item_repository.get_by_id(item_id)
        if not item:
            raise AppException("Inventory item not found", status_code=404)
        return item

    async def create_item(self, payload: ItemCreate) -> InventoryItem:
        existing = await self.item_repository.get_by_sku(payload.sku)
        if existing:
            raise AppException("SKU already exists", status_code=409)

        item = InventoryItem(**payload.model_dump())
        created = await self.item_repository.create(item)
        await self.redis.incr(self._items_version_key())
        return created

    async def update_item(self, item_id: int, payload: ItemUpdate) -> InventoryItem:
        item = await self.get_item_model_or_404(item_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, key, value)

        updated = await self.item_repository.update(item)
        await self.redis.incr(self._items_version_key())
        await self.redis.delete(self._item_key(item_id))
        return updated
