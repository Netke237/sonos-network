import os
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://sonos:sonos_network_pw@192.168.55.60:5434/sonos_network",
)


class Base(DeclarativeBase):
    pass


def build_engine_and_sessionmaker(
    database_url: str | None = None,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    url = database_url or DEFAULT_DATABASE_URL
    engine = create_async_engine(url, echo=False, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, session_factory
