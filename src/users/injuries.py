import logging
from datetime import datetime, timezone

from src.users.models import Injuries
from src.users.crud import add_record, get_record_by_id, get_records_by_user, update_record

logger = logging.getLogger(__name__)

SEVERITY_LEVELS = ['licht', 'matig', 'ernstig']

__all__ = ['SEVERITY_LEVELS', 'save_injury', 'get_active_injuries', 'resolve_injury', 'serialize_injury']

async def save_injury(data: dict) -> bool:
    try:
        data.setdefault("is_active", True)
        logger.info(f"Saving injury data: {data}")
        status = await add_record(Injuries, data)
        return True if status else False
    except Exception as e:
        logger.error(f"Error saving injury data: {e}, {data}")
        return False

async def get_active_injuries(user_id: str) -> list[Injuries]:
    injuries = await get_records_by_user(Injuries, user_id)
    return [injury for injury in injuries if injury.is_active]

async def resolve_injury(injury_id: str) -> bool:
    injury = await get_record_by_id(Injuries, injury_id)
    if not injury:
        logger.warning(f"No injury found with id {injury_id}")
        return False

    status = await update_record(Injuries, injury_id, {
        "is_active": False,
        "resolved_at": datetime.now(timezone.utc).date()
    })
    return True if status else False

def serialize_injury(injury: Injuries) -> dict:
    return {
        "affected_area": injury.affected_area,
        "description": injury.description,
        "severity": injury.severity,
        "started_at": injury.started_at.isoformat() if injury.started_at else None,
    }
