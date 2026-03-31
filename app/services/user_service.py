import math

from app.schemas.user import PaginatedUserRead, UserRead
from app.core.exceptions import AppException
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def get_user_or_404(self, user_id: int):
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise AppException("User not found", status_code=404)
        return user

    async def list_users(self, page: int = 1, page_size: int = 20) -> PaginatedUserRead:
        offset = (page - 1) * page_size
        users = await self.user_repository.list_users(offset=offset, limit=page_size)
        total_items = await self.user_repository.count_users()
        total_pages = math.ceil(total_items / page_size) if total_items else 0
        return PaginatedUserRead(
            items=[UserRead.model_validate(user) for user in users],
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    async def get_user(self, user_id: int):
        user=await self.user_repository.get_by_id(user_id)
        if not user:
            raise AppException("User not found", status_code=404)
        return user
    async def delete_user(self, user_id: int, full_name: str):
        user=await self.user_repository.get_by_id(user_id)
        if not user:
            raise AppException("Not found",status_code=404)
        
        if user.full_name != full_name:
            raise AppException("Name does not match",status_code=400)
        if not user.is_active:
            raise AppException("User is already inactive",status_code=400)
        user.is_active=False
        return await self.user_repository.delete(user)
