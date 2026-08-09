from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import Base


ModelType = TypeVar(
    "ModelType",
    bound=Base,
)


class BaseRepository(Generic[ModelType]):
    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
    ) -> None:
        self.session = session
        self.model = model

    async def get(
        self,
        object_id: int,
    ) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(
                self.model.id == object_id
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        **kwargs: Any,
    ) -> ModelType:
        obj = self.model(**kwargs)

        self.session.add(obj)

        await self.session.flush()

        return obj

    async def delete(
        self,
        obj: ModelType,
    ) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def save(
        self,
        obj: ModelType,
    ) -> ModelType:
        self.session.add(obj)

        await self.session.flush()

        return obj
