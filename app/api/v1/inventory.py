from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import (
    get_current_user,
    get_inventory_service,
    get_item_service,
    require_roles,
)
from app.models.user import User, UserRole
from app.schemas.item import ItemQuantityTotalRead
from app.schemas.movement import StockMovementCreate, StockMovementRead
from app.services.inventory_service import InventoryService
from app.services.item_service import ItemService
from app.schemas.item import ItemRead

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post(
    "/movements",
    response_model=StockMovementRead,
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.staff))],
)
async def create_stock_movement(
    payload: StockMovementCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> StockMovementRead:
    movement = await inventory_service.move_stock(payload, current_user.id)
    return StockMovementRead.model_validate(movement)


@router.get(
    "/items/total-quantity",
    response_model=ItemQuantityTotalRead,
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager))],
)
async def get_total_quantity(
    item_service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemQuantityTotalRead:
    return await item_service.get_total_quantity()


@router.get(
    "/items/{item_id}/movements",
    response_model=list[StockMovementRead],
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.staff))],
)
async def list_item_movements(
    item_id: int,
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> list[StockMovementRead]:
    rows = await inventory_service.list_item_movements(item_id)
    return [StockMovementRead.model_validate(row) for row in rows]


@router.get("/items",response_model=list[ItemRead],
            dependencies=[Depends(require_roles(UserRole.admin,UserRole.manager,UserRole.staff))]
)
async def list_inventory_items(
    item_service: Annotated[ItemService, Depends(get_item_service)],
) -> list[ItemRead]:
    return await item_service.list_items()