from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.product import ProductCreate, ProductRead
from src.core.database import get_db
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.product_repository import ProductRepository
from src.domain.exceptions import BatchNotFoundError, ProductAlreadyExistsError
from src.domain.services.product_service import ProductService


router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(
        product_repo=ProductRepository(session),
        batch_repo=BatchRepository(session),
    )
    try:
        product = await service.create_product(payload)
    except BatchNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProductAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

    await session.commit()
    return product
