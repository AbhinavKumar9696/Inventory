from datetime import timedelta

from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def register_user(self, user_data: UserCreate) -> User:
        existing = await self.user_repository.get_by_email(user_data.email)
        if existing:
            raise AppException("User with this email already exists", status_code=409)

        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
        )
        return await self.user_repository.create(user)

    async def authenticate(self, email: str, password: str, expires_minutes: int) -> TokenResponse:
        user = await self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AppException("Invalid credentials", status_code=401)
        if not user.is_active:
            raise AppException("User is inactive", status_code=403)

        token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=expires_minutes),
        )
        return TokenResponse(access_token=token)

