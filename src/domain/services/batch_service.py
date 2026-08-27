from datetime import date, datetime

from sqlalchemy.exc import IntegrityError

from src.api.v1.schemas.batch import BatchCreate, BatchUpdate
from src.data.models.batch import Batch
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.work_center_repository import WorkCenterRepository
from src.domain.exceptions import BatchAlreadyExistsError, BatchNotFoundError


class BatchService:
    def __init__(
        self,
        batch_repo: BatchRepository,
        work_center_repo: WorkCenterRepository,
    ):
        self.batch_repo = batch_repo
        self.work_center_repo = work_center_repo

    async def create_batch(self, data: BatchCreate) -> Batch:
        work_center = await self.work_center_repo.get_by_identifier(
            data.work_center_identifier
        )
        if work_center is None:
            work_center = await self.work_center_repo.create(
                identifier=data.work_center_identifier,
                name=data.work_center_name,
            )

        batch = Batch(
            is_closed=data.is_closed,
            task_description=data.task_description,
            work_center_id=work_center.id,
            shift=data.shift,
            team=data.team,
            batch_number=data.batch_number,
            batch_date=data.batch_date,
            nomenclature=data.nomenclature,
            ekn_code=data.ekn_code,
            shift_start=data.shift_start,
            shift_end=data.shift_end,
            products=[],
        )

        try:
            return await self.batch_repo.create(batch)
        except IntegrityError as e:
            if e.orig.diag.constraint_name == "uq_batch_number_date":
                raise BatchAlreadyExistsError(
                    f"Партия №{data.batch_number} за {data.batch_date} уже существует"
                )
            raise

    async def get_batch(self, batch_id: int) -> Batch:
        batch = await self.batch_repo.get_by_id(batch_id)
        if batch is None:
            raise BatchNotFoundError(f"Batch {batch_id} not found")
        return batch

    async def update_batch(self, batch_id: int, data: BatchUpdate) -> Batch:
        batch = await self.batch_repo.get_by_id(batch_id)
        if batch is None:
            raise BatchNotFoundError(f"Batch {batch_id} not found")

        updates = data.model_dump(exclude_unset=True)

        if "is_closed" in updates:
            new_value = updates["is_closed"]
            batch.is_closed = new_value
            if new_value is True:
                batch.closed_at = datetime.now()
            else:
                batch.closed_at = None

        for field, value in updates.items():
            if field == "is_closed":
                continue
            setattr(batch, field, value)

        return await self.batch_repo.update(batch)

    async def list_batches(
        self,
        is_closed: bool | None = None,
        batch_number: int | None = None,
        batch_date: date | None = None,
        work_center_identifier: str | None = None,
        shift: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Batch]:
        return await self.batch_repo.list_batches(
            is_closed=is_closed,
            batch_number=batch_number,
            batch_date=batch_date,
            work_center_identifier=work_center_identifier,
            shift=shift,
            offset=offset,
            limit=limit,
        )