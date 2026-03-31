from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import AppException
from app.core.security import hash_password, verify_password
from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_user_hashes_password_and_persists(user_factory):
    repo = AsyncMock()
    repo.get_by_email.return_value = None
    repo.create.side_effect = lambda user: user
    service = AuthService(repo)
    payload = UserCreate(
        email="new@example.com",
        full_name="New User",
        password="Secret123!",
        role=UserRole.manager,
    )

    created = await service.register_user(payload)

    assert created.email == payload.email
    assert created.full_name == payload.full_name
    assert created.role == payload.role
    assert created.hashed_password != payload.password
    assert verify_password(payload.password, created.hashed_password)
    repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate_email():
    repo = AsyncMock()
    repo.get_by_email.return_value = object()
    service = AuthService(repo)
    payload = UserCreate(
        email="existing@example.com",
        full_name="Existing User",
        password="Secret123!",
        role=UserRole.staff,
    )

    with pytest.raises(AppException) as exc:
        await service.register_user(payload)

    assert exc.value.status_code == 409
    assert exc.value.detail == "User with this email already exists"


@pytest.mark.asyncio
async def test_authenticate_rejects_invalid_credentials():
    repo = AsyncMock()
    repo.get_by_email.return_value = None
    service = AuthService(repo)

    with pytest.raises(AppException) as exc:
        await service.authenticate("missing@example.com", "bad-password", expires_minutes=15)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_authenticate_rejects_inactive_user(user_factory):
    user = user_factory(is_active=False)
    user.hashed_password = hash_password("Secret123!")
    repo = AsyncMock()
    repo.get_by_email.return_value = user
    service = AuthService(repo)

    with pytest.raises(AppException) as exc:
        await service.authenticate(user.email, "Secret123!", expires_minutes=15)

    assert exc.value.status_code == 403
    assert exc.value.detail == "User is inactive"
