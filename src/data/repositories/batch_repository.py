from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.data.models.batch import Batch
from src.data.models.work_center import WorkCenter


class BatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, batch: Batch) -> Batch:
        self.session.add(batch)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            raise
        return batch

    async def update(self, batch: Batch) -> Batch:
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            raise
        return batch

    async def get_by_id(self, batch_id: int) -> Batch | None:
        result = await self.session.execute(
            select(Batch)
            .where(Batch.id == batch_id)
            .options(selectinload(Batch.products), selectinload(Batch.work_center))
        )
        return result.scalar_one_or_none()

    async def list_batches(
        self,
        is_closed: bool | None = None,
        batch_number: int | None = None,
        batch_date: date | None = None,
        batch_date_from: date | None = None,
        batch_date_to: date | None = None,
        work_center_identifier: str | None = None,
        shift: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Batch]:
        query = select(Batch).options(
            selectinload(Batch.products), selectinload(Batch.work_center)
        )

        if is_closed is not None:
            query = query.where(Batch.is_closed == is_closed)
        if batch_number is not None:
            query = query.where(Batch.batch_number == batch_number)
        if batch_date is not None:
            query = query.where(Batch.batch_date == batch_date)
        if batch_date_from is not None:
            query = query.where(Batch.batch_date >= batch_date_from)
        if batch_date_to is not None:
            query = query.where(Batch.batch_date <= batch_date_to)
        if shift is not None:
            query = query.where(Batch.shift == shift)
        if work_center_identifier is not None:
            query = query.join(WorkCenter, WorkCenter.id == Batch.work_center_id).where(WorkCenter.identifier == work_center_identifier)

        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_expired_open_batches(self, now: datetime) -> list[Batch]:
        """Партии, которые ещё не закрыты, но их смена уже закончилась."""
        result = await self.session.execute(
            select(Batch)
            .where(Batch.is_closed == False, Batch.shift_end < now)
            .options(selectinload(Batch.products))
        )
        return list(result.scalars().all())