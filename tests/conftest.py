from pathlib import Path
import os
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DEBUG"] = "false"

from app.models.inventory_item import InventoryItem
from app.models.stock_movement import MovementType, StockMovement
from app.models.user import User, UserRole


@pytest.fixture
def user_factory() -> Callable[..., User]:
    def make_user(**overrides) -> User:
        now = datetime.now(timezone.utc)
        defaults = {
            "id": 1,
            "email": "user@example.com",
            "full_name": "Test User",
            "hashed_password": "hashed-password",
            "role": UserRole.staff,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        defaults.update(overrides)
        return User(**defaults)

    return make_user


@pytest.fixture
def item_factory() -> Callable[..., InventoryItem]:
    def make_item(**overrides) -> InventoryItem:
        now = datetime.now(timezone.utc)
        defaults = {
            "id": 1,
            "sku": "SKU-001",
            "name": "Widget",
            "description": "Test item",
            "quantity": 10,
            "reorder_level": 5,
            "unit_price": Decimal("99.99"),
            "created_at": now,
            "updated_at": now,
        }
        defaults.update(overrides)
        return InventoryItem(**defaults)

    return make_item


@pytest.fixture
def movement_factory() -> Callable[..., StockMovement]:
    def make_movement(**overrides) -> StockMovement:
        now = datetime.now(timezone.utc)
        defaults = {
            "id": 1,
            "item_id": 1,
            "quantity": 3,
            "movement_type": MovementType.in_,
            "note": "restock",
            "performed_by": 1,
            "created_at": now,
        }
        defaults.update(overrides)
        return StockMovement(**defaults)

    return make_movement


@pytest.fixture
def fake_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    redis.incr = AsyncMock()
    return redis
