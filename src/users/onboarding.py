import sqlalchemy
from typing import Optional
__all__ = ['check_onboarding']

async def check_onboarding(telegram_chat_id: str | None = None, user_id: str | None = None) -> bool:

    return False