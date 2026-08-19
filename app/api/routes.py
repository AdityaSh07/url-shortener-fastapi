from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database.database import get_db
from ..schema import URLCreate, URLResponse
from ..services.url_service import create_short_url
from ..models.url_model import URL
from ..core.config import settings

router = APIRouter()


@router.post("/shorten", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def shorten_url(
    request: URLCreate,
    db: AsyncSession = Depends(get_db),
):
    url = await create_short_url(
        db=db,
        original_url=str(request.url),
    )

    return URLResponse(
        short_code=url.short_code,
        short_url = f"{settings.base_url}/{url.short_code}",
    )



@router.get("/{short_code}")
async def redirect_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(URL).where(URL.short_code == short_code)
    )

    url = result.scalar_one_or_none()

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found",
        )

    return RedirectResponse(
        url=url.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )