from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = None
async_session = None


def init_engine():
    global engine, async_session
    if settings.database_url:
        engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=30,
            pool_recycle=1800,
        )
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )


async def get_db():
    if async_session is None:
        raise RuntimeError("Database not initialized. Set DATABASE_URL in .env")
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
