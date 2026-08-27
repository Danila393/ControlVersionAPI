from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.work_center import WorkCenter


class WorkCenterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_identifier(self, identifier: str) -> WorkCenter | None:
        result = await self.session.execute(
            select(WorkCenter).where(WorkCenter.identifier == identifier)
        )
        return result.scalar_one_or_none()

    async def create(self, identifier: str, name: str) -> WorkCenter:
        work_center = WorkCenter(identifier=identifier, name=name)
        self.session.add(work_center)
        await self.session.flush()
        return work_center