import logging
import os
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from typing import Literal, Optional

load_dotenv()

logger = logging.getLogger(__name__)

__all__ = ['HealthClient', 'get_open_wearables_user_id']

BASE_URL = os.getenv("OPEN_WEARABLES_URL", "http://api.open-wearables.homelab.local:30080")
API_KEY = os.getenv("OPEN_WEARABLES_API_KEY")
USER_ID = os.getenv("OPEN_WEARABLES_USER_ID")

HEADERS = {"X-Open-Wearables-API-Key": API_KEY}

HealthMetricType = Literal[
    'heart_rate', 'resting_heart_rate', 'heart_rate_variability_sdnn', 'heart_rate_recovery_one_minute',
    'walking_heart_rate_average', 'heart_rate_variability_rmssd', 'oxygen_saturation', 'blood_glucose',
    'blood_pressure_systolic', 'blood_pressure_diastolic', 'respiratory_rate', 'sleeping_breathing_disturbances',
    'breathing_disturbance_index', 'blood_alcohol_content', 'peripheral_perfusion_index', 'forced_vital_capacity',
    'forced_expiratory_volume_1', 'peak_expiratory_flow_rate', 'height', 'weight', 'body_fat_percentage',
    'body_mass_index', 'lean_body_mass', 'body_temperature', 'skin_temperature', 'skin_temperature_deviation',
    'skin_temperature_trend_deviation', 'waist_circumference', 'body_fat_mass', 'skeletal_muscle_mass',
    'vo2_max', 'six_minute_walk_test_distance', 'cardiovascular_age', 'steps', 'energy', 'basal_energy',
    'stand_time', 'exercise_time', 'physical_effort', 'flights_climbed', 'average_met', 'distance_walking_running',
    'distance_cycling', 'distance_swimming', 'distance_downhill_snow_sports', 'distance_other', 'walking_step_length',
    'walking_speed', 'walking_double_support_percentage', 'walking_asymmetry_percentage', 'walking_steadiness',
    'stair_descent_speed', 'stair_ascent_speed', 'running_power', 'running_speed', 'running_vertical_oscillation',
    'running_ground_contact_time', 'running_stride_length', 'swimming_stroke_count', 'underwater_depth', 'cadence',
    'power', 'speed', 'workout_effort_score', 'estimated_workout_effort_score', 'environmental_audio_exposure',
    'headphone_audio_exposure', 'environmental_sound_reduction', 'time_in_daylight', 'water_temperature',
    'uv_exposure', 'inhaler_usage', 'weather_temperature', 'weather_humidity', 'garmin_stress_level',
    'garmin_skin_temperature', 'garmin_fitness_age', 'garmin_body_battery', 'electrodermal_activity', 'push_count',
    'atrial_fibrillation_burden', 'insulin_delivery', 'number_of_times_fallen', 'number_of_alcoholic_beverages',
    'nike_fuel', 'hydration'
]

async def get_open_wearables_user_id(firstname, lastname) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/users",
                headers=HEADERS
            )

            users = response.json().get("items", [])
            for user in users:
                if user.get("first_name", "") == firstname and user.get("last_name", "") == lastname:
                    return user

    except Exception as er:
        logger.warning(f"Failed to get user_id from {firstname} {lastname}; error: {er}")


class HealthClient:

    def __init__(self, user_id: str):
        self.user_id = user_id

    @staticmethod
    def _get_date_range(days_back: int = 1):
        end = datetime.now(timezone.utc).date() + timedelta(days=1)
        start = end - timedelta(days=days_back + 1)
        return str(start), str(end)

    @staticmethod
    def _safe_avg(values: list) -> float | None:
        return sum(values) / len(values) if values else None

    async def get_sleep(self, days_back: int = 1) -> dict:
        start, end = self._get_date_range(days_back)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/users/{self.user_id}/summaries/sleep",
                headers=HEADERS,
                params={"start_date": start, "end_date": end}
            )
            return response.json()

    async def get_sum(self, days_back: int = 1) -> dict:
        start, end = self._get_date_range(days_back)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/users/{self.user_id}/summaries/data",
                headers=HEADERS,
                params={"start_date": start, "end_date": end}
            )
            return response.json()

    async def get_morning_context(self) -> dict:
        sleep_data = await self.get_sleep(days_back=1)
        recovery_data = await self.get_recovery_score(sleep_data)

        sleep = sleep_data.get("data", [])
        latest_sleep = sleep[-1] if sleep else {}

        return {
            "scenario": "morning_check_in",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sleep": {
                "duration_minutes": latest_sleep.get("duration_minutes"),
                "duration_hours": round(latest_sleep.get("duration_minutes", 0) / 60, 2),
                "time_in_bed_minutes": latest_sleep.get("time_in_bed_minutes"),
                "efficiency_percent": latest_sleep.get("efficiency_percent"),
                "stages": latest_sleep.get("stages"),
                "avg_hrv_sdnn_ms": latest_sleep.get("avg_hrv_sdnn_ms")
            },
            "recovery": {
                "recovery_score": recovery_data.get("recovery_score")
            }
        }

    async def get_evening_context(self) -> dict:
        activity_data = await self.get_activity(days_back=1)
        workout_data = await self.get_workouts(days_back=2)

        activity = activity_data.get("data", [])
        workout = workout_data.get("data", [])

        latest_activity = activity[-1] if activity else {}

        workouts = await self.get_workout_context()

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

    async def get_workout_context(self) -> dict:
        workout_data = await self.get_workouts(days_back=1)
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

    async def get_timeseries(self, days_back: int = 1, types: HealthMetricType = "resting_heart_rate") -> dict:
        start, end = self._get_date_range(days_back=days_back)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/users/{self.user_id}/timeseries",
                headers=HEADERS,
                params={"start_time": start,
                        "end_time": end,
                        "types": types}

            )
            return response.json().get("data", [])

    async def get_recovery_score(self, sleep_data_day: dict) -> dict:
        baseline = await self.get_baseline()

        hrv_task = self.get_timeseries(1, 'heart_rate_variability_sdnn')
        rhr_task = self.get_timeseries(1, 'resting_heart_rate')

        hrv_day, rhr_day = await asyncio.gather(hrv_task, rhr_task)

        hrv_values = [item["value"] for item in hrv_day if "value" in item]
        hrv_today = self._safe_avg(hrv_values)
        hrv_score = min((hrv_today / baseline['avg_hrv']) if hrv_today and baseline['avg_hrv'] else 1.0, 1.0)

        rhr_values = [item["value"] for item in rhr_day if "value" in item]
        rhr_today = self._safe_avg(rhr_values)
        rhr_score = min((baseline['avg_rhr'] / rhr_today) if rhr_today and baseline['avg_rhr'] else 1.0, 1.0)

        sleep_values = sleep_data_day.get("data", [])
        sleep_values = sleep_values[0] if sleep_values else {}
        duration_minutes = sleep_values.get('duration_minutes', 0)
        duration_score = min(duration_minutes / (8 * 60), 1)
        efficiency_percent = sleep_values.get("efficiency_percent", 0)
        efficiency_score = min(efficiency_percent / 100, 1)
        sleep_score = (duration_score * 0.6) + (efficiency_score * 0.4)

        recovery_score = ((hrv_score * 0.5) + (rhr_score * 0.3) + (sleep_score * 0.2)) * 100
        recovery_score = max(0.0, min(recovery_score, 100.0))

        return {
            "hrv_score": hrv_score,
            "rhr_score": rhr_score,
            "sleep_score": sleep_score,
            "recovery_score": recovery_score
        }

    async def get_workouts(self, days_back: int = 7) -> dict:
        start, end = self._get_date_range(days_back)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/users/{self.user_id}/events/workouts",
                headers=HEADERS,
                params={"start_date": start, "end_date": end}
            )
            return response.json()

    async def get_health_score(self, days_back: int = 1) -> dict:
        start, end = self.get_date_range(days_back)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/users/{self.user_id}/health-scores",
                headers=HEADERS,
                params={"start_date": start, "end_date": end}
            )
            return response.json()

    async def get_activity(self, days_back: int = 1) -> dict:
        start, end = self._get_date_range(days_back)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/users/{self.user_id}/summaries/activity",
                headers=HEADERS,
                params={"start_date": start, "end_date": end}
            )
            return response.json()



    async def get_baseline(self) -> dict:
        hrv_task = self.get_timeseries(14, 'heart_rate_variability_sdnn')
        rhr_task = self.get_timeseries(14, 'resting_heart_rate')
        sleep_task = self.get_sleep(14)

        heart_rate_variability, resting_heart_rate, sleep = await asyncio.gather(
            hrv_task, rhr_task, sleep_task
        )

        hrv_values = [item["value"] for item in heart_rate_variability if "value" in item]
        rhr_values = [item["value"] for item in resting_heart_rate if "value" in item]

        sleep_logs = sleep.get('data', [])

        sleep_duration = []
        sleep_efficiency = []
        awake_duration = []
        light_duration = []
        deep_duration = []
        rem_duration = []

        for log in sleep_logs:
            sleep_duration.append(log.get('duration_minutes', 0))
            sleep_efficiency.append(log.get('efficiency_percent', 0))

            stages = log.get('stages', {})
            awake_duration.append(stages.get('awake_minutes', 0))
            light_duration.append(stages.get('light_minutes', 0))
            deep_duration.append(stages.get('deep_minutes', 0))
            rem_duration.append(stages.get('rem_minutes', 0))

        avg_sleep_duration = self._safe_avg(sleep_duration)

        return {
            "avg_hrv": self._safe_avg(hrv_values),
            "avg_rhr": self._safe_avg(rhr_values),
            "avg_sleep_duration": avg_sleep_duration,
            "avg_sleep_duration_hours": avg_sleep_duration / 60 if avg_sleep_duration else 0.0,
            "avg_sleep_efficiency": self._safe_avg(sleep_efficiency),
            "avg_awake_duration": self._safe_avg(awake_duration),
            "avg_light_duration": self._safe_avg(light_duration),
            "avg_deep_duration": self._safe_avg(deep_duration),
            "avg_rem_duration": self._safe_avg(rem_duration)
        }