from unittest.mock import AsyncMock, Mock

import pytest

from app.core.exceptions import AppException
from app.models.stock_movement import MovementType
from app.schemas.movement import StockMovementCreate
from app.services.inventory_service import InventoryService


@pytest.mark.asyncio
async def test_move_stock_raises_when_item_missing(fake_redis):
    item_repo = AsyncMock()
    item_repo.get_by_id.return_value = None
    movement_repo = AsyncMock()

    service = InventoryService(item_repo, movement_repo, fake_redis)
    payload = StockMovementCreate(item_id=1, quantity=2, movement_type=MovementType.in_)

    with pytest.raises(AppException) as exc:
        await service.move_stock(payload, user_id=7)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Inventory item not found"


@pytest.mark.asyncio
async def test_move_stock_rejects_insufficient_quantity(fake_redis, item_factory):
    item = item_factory(quantity=1)
    item_repo = AsyncMock()
    item_repo.get_by_id.return_value = item
    movement_repo = AsyncMock()

    service = InventoryService(item_repo, movement_repo, fake_redis)
    payload = StockMovementCreate(item_id=item.id, quantity=3, movement_type=MovementType.out)

    with pytest.raises(AppException) as exc:
        await service.move_stock(payload, user_id=7)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Insufficient stock"


@pytest.mark.asyncio
async def test_move_stock_updates_quantity_invalidates_cache_and_sends_alert(
    fake_redis, item_factory, movement_factory, monkeypatch
):
    item = item_factory(quantity=6, reorder_level=5)
    created_movement = movement_factory(item_id=item.id, movement_type=MovementType.out, quantity=2)
    item_repo = AsyncMock()
    item_repo.get_by_id.return_value = item
    item_repo.update.return_value = item
    movement_repo = AsyncMock()
    movement_repo.create.return_value = created_movement
    alert_mock = Mock()
    monkeypatch.setattr("app.services.inventory_service.send_low_stock_alert.delay", alert_mock)

    service = InventoryService(item_repo, movement_repo, fake_redis)
    payload = StockMovementCreate(item_id=item.id, quantity=2, movement_type=MovementType.out)

    result = await service.move_stock(payload, user_id=11)

    assert result is created_movement
    assert item.quantity == 4
    item_repo.update.assert_awaited_once_with(item)
    movement_repo.create.assert_awaited_once()
    fake_redis.delete.assert_awaited_once_with("inventory:items:all", f"inventory:item:{item.id}")
    alert_mock.assert_called_once_with(item.id, item.sku, item.quantity, item.reorder_level)
