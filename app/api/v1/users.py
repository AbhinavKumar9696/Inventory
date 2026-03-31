from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_user_service, require_roles
from app.models.user import User, UserRole
from app.schemas.user import PaginatedUserRead, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def read_me(
    current_user: Annotated[
        User, Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.staff))
    ],
) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get(
    "/",
    response_model=PaginatedUserRead,
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager))],
)
async def list_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedUserRead:
    return await user_service.list_users(page=page, page_size=page_size)


@router.get("/{user_id}", 
            response_model=UserRead,
            dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager))]
)
async def get_user(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    user = await user_service.get_user(user_id)
    return UserRead.model_validate(user)


@router.delete(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_roles(UserRole.admin,UserRole.manager))]
)
async def delete_user(
    user_id: int,
    full_name: str,
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserRead:
    user =await user_service.delete_user(user_id ,full_name)
    return UserRead.model_validate(user)
