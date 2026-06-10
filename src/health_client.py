import os
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("OPEN_WEARABLES_URL", "http://api.open-wearables.homelab.local:30080")
API_KEY = os.getenv("OPEN_WEARABLES_API_KEY")
USER_ID = os.getenv("OPEN_WEARABLES_USER_ID")

HEADERS = {"X-Open-Wearables-API-Key": API_KEY}


def get_date_range(days_back: int = 1):
    end = datetime.now(timezone.utc).date() + timedelta(days=1)
    start = end - timedelta(days=days_back + 1)
    return str(start), str(end)

async def get_sleep(days_back: int = 1) -> dict:
    start, end = get_date_range(days_back)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/users/{USER_ID}/summaries/sleep",
            headers=HEADERS,
            params={"start_date": start, "end_date": end}
        )
        return response.json()

async def get_sum(days_back: int = 1) -> dict:
    start, end = get_date_range(days_back)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/users/{USER_ID}/summaries/data",
            headers=HEADERS,
            params={"start_date": start, "end_date": end}
        )
        return response.json()

async def get_morning_context() -> dict:
    sleep_data = await get_sleep(days_back=1)
    recovery_data = await get_recovery(days_back=1)

    sleep = sleep_data.get("data", [])
    recovery = recovery_data.get("data", [])

    latest_sleep = sleep[-1] if sleep else {}
    latest_recovery = recovery[-1] if recovery else {}

    return {
        "sleep": {
            "duration_minutes": latest_sleep.get("duration_minutes"),
            "efficiency_percent": latest_sleep.get("efficiency_percent"),
            "stages": latest_sleep.get("stages"),
            "avg_hrv_sdnn_ms": latest_sleep.get("avg_hrv_sdnn_ms"),
            "avg_heart_rate_bpm": latest_sleep.get("avg_heart_rate_bpm"),
        },
        "recovery": {
            "recovery_score": latest_recovery.get("recovery_score"),
            "resting_heart_rate_bpm": latest_recovery.get("resting_heart_rate_bpm"),
            "avg_hrv_sdnn_ms": latest_recovery.get("avg_hrv_sdnn_ms"),
        }
    }

async def get_evening_context() -> dict:
    activity_data = await get_activity(days_back=1)
    workout_data = await get_workouts(days_back=2)

    activity = activity_data.get("data", [])
    workout = workout_data.get("data", [])

    latest_activity = activity[-1] if activity else {}

    workouts = [
        {
            "type": w.get("type"),
            "start_time": w.get("start_time"),
            "end_time": w.get("end_time"),
            "duration_seconds": w.get("duration_seconds"),
            "distance_meters": w.get("distance_meters"),
            "calories_kcal": w.get("calories_kcal"),
            "avg_heart_rate_bpm": w.get("avg_heart_rate_bpm"),
            "max_heart_rate_bpm": w.get("max_heart_rate_bpm"),
            "avg_pace_sec_per_km": w.get("avg_pace_sec_per_km"),
            "elevation_gain_meters": w.get("elevation_gain_meters")
        }
        for w in workout
    ]

    return {
        "activity": {
            "steps": latest_activity.get("steps"),
            "distance_meters": latest_activity.get("distance_meters"),
            "floors_climbed": latest_activity.get("floors_climbed"),
            "elevation_meters": latest_activity.get("elevation_meters"),
            "active_calories_kcal": latest_activity.get("active_calories_kcal"),
            "total_calories_kcal": latest_activity.get("total_calories_kcal"),
            "active_minutes": latest_activity.get("active_minutes"),
            "sedentary_minutes": latest_activity.get("sedentary_minutes"),
            "intensity_minutes": latest_activity.get("intensity_minutes"),
            "heart_rate": latest_activity.get("heart_rate")
        },
        "workouts": workouts
    }

async def get_workout_context() -> dict:
    workout_data = await get_workouts(days_back=1)
    workout = workout_data.get("data", [])

    return {
        "workouts": [
            {
                "type": w.get("type"),
                "start_time": w.get("start_time"),
                "end_time": w.get("end_time"),
                "duration_seconds": w.get("duration_seconds"),
                "distance_meters": w.get("distance_meters"),
                "calories_kcal": w.get("calories_kcal"),
                "avg_heart_rate_bpm": w.get("avg_heart_rate_bpm"),
                "max_heart_rate_bpm": w.get("max_heart_rate_bpm"),
                "avg_pace_sec_per_km": w.get("avg_pace_sec_per_km"),
                "elevation_gain_meters": w.get("elevation_gain_meters")
            }
            for w in workout
        ]
    }

async def get_recovery(days_back: int = 1) -> dict:
    start, end = get_date_range(days_back)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/users/{USER_ID}/summaries/recovery",
            headers=HEADERS,
            params={"start_date": start, "end_date": end}
        )
        return response.json()


async def get_workouts(days_back: int = 7) -> dict:
    start, end = get_date_range(days_back)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/users/{USER_ID}/events/workouts",
            headers=HEADERS,
            params={"start_date": start, "end_date": end}
        )
        return response.json()

async def get_health_score(days_back: int = 1) -> dict:
    start, end = get_date_range(days_back)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/users/{USER_ID}/health-scores",
            headers=HEADERS,
            params={"start_date": start, "end_date": end}
        )
        return response.json()

async def get_activity(days_back: int = 1) -> dict:
    start, end = get_date_range(days_back)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/users/{USER_ID}/summaries/activity",
            headers=HEADERS,
            params={"start_date": start, "end_date": end}
        )
        return response.json()