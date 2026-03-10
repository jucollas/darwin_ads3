from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency de FastAPI: 1 sesión por request.
    """
    async with AsyncSessionLocal() as session:
        yield session