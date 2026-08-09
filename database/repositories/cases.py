from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Case,
    CaseOpen,
    CaseReward,
)


class CaseRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # CASES
    # =====================================================

    async def get_case(
        self,
        case_id: int,
    ) -> Case | None:

        result = await self.session.execute(
            select(Case).where(
                Case.id == case_id
            )
        )

        return result.scalar_one_or_none()

    async def get_active_cases(
        self,
    ) -> list[Case]:

        result = await self.session.execute(
            select(Case)
            .where(
                Case.enabled == True
            )
            .order_by(
                Case.sort_order.asc(),
                Case.id.asc(),
            )
        )

        return list(
            result.scalars().all()
        )

    async def create_case(
        self,
        **kwargs,
    ) -> Case:

        case = Case(
            **kwargs
        )

        self.session.add(
            case
        )

        await self.session.flush()

        return case

    async def update_case(
        self,
        case: Case,
        **kwargs,
    ) -> Case:

        for key, value in kwargs.items():

            if hasattr(case, key):
                setattr(
                    case,
                    key,
                    value,
                )

        await self.session.flush()

        return case

    async def delete_case(
        self,
        case: Case,
    ) -> None:

        await self.session.delete(
            case
        )

        await self.session.flush()

    # =====================================================
    # REWARDS
    # =====================================================

    async def get_rewards(
        self,
        case_id: int,
    ) -> list[CaseReward]:

        result = await self.session.execute(
            select(CaseReward)
            .where(
                CaseReward.case_id
                == case_id,
                CaseReward.enabled
                == True,
            )
            .order_by(
                CaseReward.sort_order.asc(),
                CaseReward.id.asc(),
            )
        )

        return list(
            result.scalars().all()
        )

    async def get_reward(
        self,
        reward_id: int,
    ) -> CaseReward | None:

        result = await self.session.execute(
            select(CaseReward).where(
                CaseReward.id
                == reward_id
            )
        )

        return result.scalar_one_or_none()

    async def create_reward(
        self,
        **kwargs,
    ) -> CaseReward:

        reward = CaseReward(
            **kwargs
        )

        self.session.add(
            reward
        )

        await self.session.flush()

        return reward

    async def update_reward(
        self,
        reward: CaseReward,
        **kwargs,
    ) -> CaseReward:

        for key, value in kwargs.items():

            if hasattr(reward, key):
                setattr(
                    reward,
                    key,
                    value,
                )

        await self.session.flush()

        return reward

    async def delete_reward(
        self,
        reward: CaseReward,
    ) -> None:

        await self.session.delete(
            reward
        )

        await self.session.flush()

    # =====================================================
    # CASE HISTORY
    # =====================================================

    async def create_open(
        self,
        **kwargs,
    ) -> CaseOpen:

        opened = CaseOpen(
            **kwargs
        )

        self.session.add(
            opened
        )

        await self.session.flush()

        return opened

    async def get_user_history(
        self,
        user_id: int,
        limit: int = 50,
    ) -> list[CaseOpen]:

        result = await self.session.execute(
            select(CaseOpen)
            .where(
                CaseOpen.user_id
                == user_id
            )
            .order_by(
                CaseOpen.created_at.desc()
            )
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )
