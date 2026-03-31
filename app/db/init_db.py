import logging

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


async def seed_default_admin(user_repo: UserRepository) -> None:
    settings = get_settings()
    existing = await user_repo.get_by_email(settings.default_admin_email)
    if existing:
        return

    admin = User(
        email=settings.default_admin_email,
        full_name="Default Admin",
        hashed_password=hash_password(settings.default_admin_password),
        role=UserRole.admin,
        is_active=True,
    )
    await user_repo.create(admin)
    logger.info("Seeded default admin user.")

