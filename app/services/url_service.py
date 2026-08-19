from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models.url_model import URL
import secrets
import string


def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    random_part = "".join(
        secrets.choice(characters)
        for _ in range(length)
    )

    return random_part


async def create_short_url(
    db: AsyncSession,
    original_url: str,
) -> URL:

    for _ in range(3):
        short_code = generate_short_code()

        url = URL(
            original_url=original_url,
            short_code=short_code,
        )

        db.add(url)

        try:
            await db.commit()
            await db.refresh(url)

            return url

        except IntegrityError:
            await db.rollback()

    raise RuntimeError("Could not generate a unique short code")