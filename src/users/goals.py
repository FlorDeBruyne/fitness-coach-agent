import logging
from datetime import datetime, timezone

from src.users.models import Goals
from src.users.crud import add_record, get_record_by_id, get_records_by_user, update_record

logger = logging.getLogger(__name__)

__all__ = ['save_goal', 'get_active_goals', 'complete_goal']

async def save_goal(data: dict) -> bool:
    try:
        data.setdefault("status", "active")
        data.setdefault("current_value", 0)
        logger.info(f"Saving goal data: {data}")
        status = await add_record(Goals, data)
        return True if status else False
    except Exception as e:
        logger.error(f"Error saving goal data: {e}, {data}")
        return False

async def get_active_goals(user_id: str) -> list[Goals]:
    goals = await get_records_by_user(Goals, user_id)
    return [goal for goal in goals if goal.status == "active"]

async def complete_goal(goal_id: str) -> bool:
    goal = await get_record_by_id(Goals, goal_id)
    if not goal:
        logger.warning(f"No goal found with id {goal_id}")
        return False

    status = await update_record(Goals, goal_id, {
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).replace(tzinfo=None)
    })
    return True if status else False
