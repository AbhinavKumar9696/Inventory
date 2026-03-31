import pytest
from unittest.mock import AsyncMock

from app.core.exceptions import AppException
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_get_user_returns_user(user_factory):
    user = user_factory()
    repo = AsyncMock()
    repo.get_by_id.return_value = user

    service = UserService(repo)

    result = await service.get_user(user.id)

    assert result is user


@pytest.mark.asyncio
async def test_list_users_returns_paginated_result(user_factory):
    users = [user_factory(id=1), user_factory(id=2, email="user2@example.com")]
    repo = AsyncMock()
    repo.list_users.return_value = users
    repo.count_users.return_value = 7

    service = UserService(repo)

    result = await service.list_users(page=2, page_size=2)

    assert result.page == 2
    assert result.page_size == 2
    assert result.total_items == 7
    assert result.total_pages == 4
    assert [user.id for user in result.items] == [1, 2]
    repo.list_users.assert_awaited_once_with(offset=2, limit=2)
    repo.count_users.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_raises_for_missing_user():
    repo = AsyncMock()
    repo.get_by_id.return_value = None

    service = UserService(repo)

    with pytest.raises(AppException) as exc:
        await service.get_user(99)

    assert exc.value.status_code == 404
    assert exc.value.detail == "User not found"


@pytest.mark.asyncio
async def test_delete_user_marks_user_inactive_and_calls_repository(user_factory):
    user = user_factory()
    repo = AsyncMock()
    repo.get_by_id.return_value = user
    repo.delete.return_value = user

    service = UserService(repo)

    result = await service.delete_user(user.id, user.full_name)

    assert result is user
    assert user.is_active is False
    repo.delete.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_delete_user_rejects_name_mismatch(user_factory):
    user = user_factory(full_name="Correct Name")
    repo = AsyncMock()
    repo.get_by_id.return_value = user

    service = UserService(repo)

    with pytest.raises(AppException) as exc:
        await service.delete_user(user.id, "Wrong Name")

    assert exc.value.status_code == 400
    assert exc.value.detail == "Name does not match"


@pytest.mark.asyncio
async def test_delete_user_rejects_inactive_user(user_factory):
    user = user_factory(is_active=False)
    repo = AsyncMock()
    repo.get_by_id.return_value = user

    service = UserService(repo)

    with pytest.raises(AppException) as exc:
        await service.delete_user(user.id, user.full_name)

    assert exc.value.status_code == 400
    assert exc.value.detail == "User is already inactive"
