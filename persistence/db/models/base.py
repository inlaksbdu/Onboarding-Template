import ssl

# import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import URL
from .db_model_base import Base

# Set the event loop policy to WindowsSelectorEventLoopPolicy
# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from persistence.db.configuration.config import get_auth_config

config = get_auth_config()


"""
Use asyncpg driver for postgres configuration
"""

SQLALCHEMY_DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=config.database_username,
    password=config.database_password,
    host=config.database_host,
    port=config.database_port,
    database=config.database_name,
)

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def create_db_engine():
    # return create_async_engine(
    #     database_connection_string, poolclass=NullPool, echo=True, future=True
    # )
    return create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=True,
        future=True,
        connect_args={"ssl": ssl_context},
    )


engine = create_db_engine()

# Asynchronous session factory
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
