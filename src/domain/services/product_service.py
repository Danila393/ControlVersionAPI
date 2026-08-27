from datetime import datetime, UTC

from sqlalchemy.exc import IntegrityError

from src.api.v1.schemas.product import ProductCreate
from src.data.models.product import Product
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.product_repository import ProductRepository
from src.domain.exceptions import (
    BatchNotFoundError,
    ProductAlreadyAggregatedError,
    ProductAlreadyExistsError,
    ProductNotFoundError,
)


class ProductService:
    def __init__(
        self,
        product_repo: ProductRepository,
        batch_repo: BatchRepository,
    ):
        self.product_repo = product_repo
        self.batch_repo = batch_repo

    async def create_product(self, data: ProductCreate) -> Product:
        batch = await self.batch_repo.get_by_id(data.batch_id)
        if batch is None:
            raise BatchNotFoundError(f"Batch {data.batch_id} not found")

        product = Product(batch_id=data.batch_id, unique_code=data.unique_code)

        try:
            return await self.product_repo.create(product)
        except IntegrityError as e:
            if e.orig.diag.constraint_name == "ix_products_unique_code":
                raise ProductAlreadyExistsError(
                    f"Продукция с кодом {data.unique_code} уже существует"
                )
            raise

    async def aggregate_product(self, batch_id: int, unique_code: str) -> Product:
        product = await self.product_repo.get_by_unique_code(unique_code)
        if product is None or product.batch_id != batch_id:
            raise ProductNotFoundError(
                f"Продукция с кодом {unique_code} не найдена в партии {batch_id}"
            )
        if product.is_aggregated is True:
            raise ProductAlreadyAggregatedError(
                f"Продукт с кодом {unique_code} уже аггрегирован"
            )
        else:
            product.is_aggregated = True
            product.aggregated_at=datetime.now(UTC)

        return await self.product_repo.update(product)
