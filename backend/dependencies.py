from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from database.models import User
from database.session import get_session


async def get_user_by_telegram_id(
    telegram_id: int,
) -> Optional[User]:

    async with get_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        return result.scalar_one_or_none()
