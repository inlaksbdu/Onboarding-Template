import ssl

# import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from Library.config import settings
from sqlalchemy.orm import sessionmaker
# Set the event loop policy to WindowsSelectorEventLoopPolicy
# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

config = settings


"""
Use asyncpg driver for postgres configuration
"""

database_connection_string = (
    f"postgresql+asyncpg://{config.database_username}"
    f":{config.database_password}@{config.database_host}"
    f"/{config.database_name}"
)

SQLALCHEMY_DATABASE_URL = database_connection_string


def create_db_engine():
    # return create_async_engine(
    #     database_connection_string, poolclass=NullPool, echo=True, future=True
    # )
    return create_async_engine(database_connection_string, echo=True, future=True)


engine = create_db_engine()

# Asynchronous session factory
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

"""
synchronous session

def create_db_engine():
    return create_engine(
        database_connection_string, poolclass=NullPool, echo=True, future=True
    )
    
    
engine = create_db_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

def get_db():
    with SessionLocal() as session:
         yield session

"""

