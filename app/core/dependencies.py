from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.db.session import get_db_session, get_redis
from app.models.user import User, UserRole
from app.repositories.item_repository import ItemRepository
from app.repositories.movement_repository import MovementRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.inventory_service import InventoryService
from app.services.item_service import ItemService
from app.services.user_service import UserService

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRepository:
    return UserRepository(session)


def get_item_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ItemRepository:
    return ItemRepository(session)


def get_movement_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MovementRepository:
    return MovementRepository(session)


def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(user_repo)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repo)


def get_item_service(
    item_repo: Annotated[ItemRepository, Depends(get_item_repository)],
    redis_client: Annotated[Redis, Depends(get_redis)],
) -> ItemService:
    return ItemService(item_repo, redis_client)


def get_inventory_service(
    item_repo: Annotated[ItemRepository, Depends(get_item_repository)],
    movement_repo: Annotated[MovementRepository, Depends(get_movement_repository)],
    redis_client: Annotated[Redis, Depends(get_redis)],
) -> InventoryService:
    return InventoryService(item_repo, movement_repo, redis_client)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        user_id = int(subject)
    except (ValueError, TypeError):
        raise AppException("Could not validate credentials", status_code=401)

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AppException("User not found", status_code=404)
    return user


def require_roles(*roles: UserRole) -> Callable[[Annotated[User, Depends(get_current_user)]], User]:
    async def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise AppException("Insufficient permissions", status_code=403)
        return current_user

    return role_checker
