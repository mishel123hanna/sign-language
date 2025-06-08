from typing import Optional
from app.db.models import User
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import UserCreateModel
from .utils import generate_hash_password


class UserService:

    async def get_user_by_email(
        self, email: str, session: AsyncSession
    ) -> Optional[User]:
        result = await session.exec(select(User).where(User.email == email))
        return result.one_or_none()

    async def get_user_by_username(
        self, username: str, session: AsyncSession
    ) -> Optional[User]:
        result = await session.exec(select(User).where(User.username == username))
        return result.one_or_none()

    async def user_exists(
        self, email: str, username: str, session: AsyncSession
    ) -> bool:
        user_by_email = await self.get_user_by_email(email, session)
        # user_by_username = await self.get_user_by_username(username, session)
        return user_by_email is not None
        # return True if user is not None else False

    async def create_user(
        self, user_data: UserCreateModel, session: AsyncSession
    ) -> User:
        user_dict = user_data.model_dump()
        hashed_password = generate_hash_password(user_dict.pop("password"))
        new_user = User(**user_dict, hashed_password=hashed_password)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

