from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_item_service, require_roles
from app.models.user import UserRole
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate, PaginatedItemRead
from app.services.item_service import ItemService

router = APIRouter(prefix="/items", tags=["Items"])


@router.get(
    "/",
    response_model=PaginatedItemRead,
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.staff))],
)
async def list_items(
    item_service: Annotated[ItemService, Depends(get_item_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedItemRead:
    return await item_service.list_items(page=page, page_size=page_size)


@router.post(
    "/",
    response_model=ItemRead,
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager))],
)
async def create_item(
    payload: ItemCreate,
    item_service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemRead:
    item = await item_service.create_item(payload)
    return ItemRead.model_validate(item)


@router.get(
    "/{item_id}",
    response_model=ItemRead,
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.staff))],
)
async def get_item(
    item_id: int,
    item_service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemRead:
    return await item_service.get_item(item_id)


@router.patch(
    "/{item_id}",
    response_model=ItemRead,
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager))],
)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    item_service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemRead:
    item = await item_service.update_item(item_id, payload)
    return ItemRead.model_validate(item)
