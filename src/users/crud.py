import os
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from typing import Any
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = str(os.getenv("DATABASE_URL"))
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

__all__ = ['add_record', 'get_record_by_id', 'get_record_by_user', 'get_record_by_telegram']

async def add_record(model_class, data: dict) -> bool:
    """
    Create database record.
    """
    async with async_session() as session:
        try:
            if "created_at" not in data:
                data["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
            if "updated_at" not in data:
                data["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

            # Initialize model with data
            record = model_class(**data)

            async with session.begin():
                session.add(record)

            logger.info(f"Record of type {model_class.__name__} created.")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Database error in {model_class.__name__}: {e}")
            await session.rollback()
            return False

async def get_record_by_id(model_class, record_id: str) -> Any | None:
    """Get a record by its Primary key ID."""
    async with async_session() as session:
        result = await session.execute(select(model_class).where(model_class.id == record_id))
        return result.scalar_one_or_none()

async def get_record_by_user(model_class, user_id: str) -> Any | None:
    """Get a record by the user ID."""
    async with async_session() as session:
        result = await session.execute(select(model_class).where(model_class.user_id == user_id))
        return result.scalar_one_or_none()

async def get_record_by_telegram(model_class, telegram_id: str) -> Any | None:
    """Get a record by the user ID."""
    async with async_session() as session:
        result = await session.execute(select(model_class).where(model_class.telegram_chat_id == telegram_id))
        return result.scalar_one_or_none()

