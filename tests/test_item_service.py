import json
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import AppException
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate
from app.services.item_service import ItemService


@pytest.mark.asyncio
async def test_list_items_returns_cached_payload(fake_redis, item_factory):
    cached_item = ItemRead.model_validate(item_factory()).model_dump(mode="json")
    fake_redis.get.side_effect = [
        "3",
        json.dumps(
            {
                "items": [cached_item],
                "page": 1,
                "page_size": 20,
                "total_items": 1,
                "total_pages": 1,
            }
        ),
    ]
    repo = AsyncMock()

    service = ItemService(repo, fake_redis)

    result = await service.list_items()

    assert len(result.items) == 1
    assert result.items[0].sku == cached_item["sku"]
    repo.list_items.assert_not_called()


@pytest.mark.asyncio
async def test_list_items_returns_paginated_result_and_caches_it(fake_redis, item_factory):
    repo = AsyncMock()
    repo.list_items.return_value = [item_factory()]
    repo.count_items.return_value = 5

    service = ItemService(repo, fake_redis)

    result = await service.list_items(page=2, page_size=2)

    assert result.page == 2
    assert result.page_size == 2
    assert result.total_items == 5
    assert result.total_pages == 3
    assert len(result.items) == 1
    repo.list_items.assert_awaited_once_with(offset=2, limit=2)
    repo.count_items.assert_awaited_once()
    fake_redis.setex.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_item_raises_for_missing_item(fake_redis):
    repo = AsyncMock()
    repo.get_by_id.return_value = None

    service = ItemService(repo, fake_redis)

    with pytest.raises(AppException) as exc:
        await service.get_item(12)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Inventory item not found"


@pytest.mark.asyncio
async def test_create_item_rejects_duplicate_sku(fake_redis):
    repo = AsyncMock()
    repo.get_by_sku.return_value = object()

    service = ItemService(repo, fake_redis)
    payload = ItemCreate(
        sku="SKU-001",
        name="Widget",
        description="Test item",
        quantity=5,
        reorder_level=2,
        unit_price=Decimal("15.50"),
    )

    with pytest.raises(AppException) as exc:
        await service.create_item(payload)

    assert exc.value.status_code == 409
    assert exc.value.detail == "SKU already exists"


@pytest.mark.asyncio
async def test_update_item_updates_fields_and_invalidates_cache(fake_redis, item_factory):
    item = item_factory(name="Old Name", unit_price=Decimal("5.00"))
    repo = AsyncMock()
    repo.get_by_id.return_value = item
    repo.update.return_value = item

    service = ItemService(repo, fake_redis)
    payload = ItemUpdate(name="New Name", unit_price=Decimal("7.50"))

    result = await service.update_item(item.id, payload)

    assert result is item
    assert item.name == "New Name"
    assert item.unit_price == Decimal("7.50")
    fake_redis.incr.assert_awaited_once_with("inventory:items:version")
    fake_redis.delete.assert_awaited_once_with(f"inventory:item:{item.id}")
