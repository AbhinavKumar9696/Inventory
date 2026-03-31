from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.core.dependencies import get_auth_service, require_roles
from app.models.user import UserRole
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager))],
)
async def register_user(
    payload: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    user = await auth_service.register_user(payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    settings = get_settings()
    return await auth_service.authenticate(
        email=form_data.username,
        password=form_data.password,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )
