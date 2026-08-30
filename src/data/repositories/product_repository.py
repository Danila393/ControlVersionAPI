from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, product: Product) -> Product:
        self.session.add(product)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            raise
        return product

    async def get_by_unique_code(self, unique_code: str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.unique_code == unique_code)
        )
        return result.scalar_one_or_none()

    async def update(self, product: Product) -> Product:
        await self.session.flush()
        return product
