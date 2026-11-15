
"""Location-based environmental analysis for EARTHTRACE."""

import os
from typing import Literal

import httpx
from pydantic import BaseModel, Field, model_validator

from .results import validate_result


class Location(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class LocationRequest(BaseModel):
    location: Location

    variables: list[
        Literal["temperature", "rainfall", "soil_moisture"]
    ] = Field(
        default_factory=lambda: [
            "temperature",
            "rainfall",
            "soil_moisture",
        ],
        min_length=1,
        max_length=3,
    )

    @model_validator(mode="after")
    def check_variables(self):
        if len(self.variables) != len(set(self.variables)):
            raise ValueError("Duplicate variables are not allowed")
        return self


def get_trend(slope: float) -> str:
    if slope > 0:
        return "increasing"
    if slope < 0:
        return "decreasing"
    return "no_linear_change"


def describe_result(variable: str, result: dict) -> str:
    trend = get_trend(result["slope"])

    significance = (
        "statistically significant"
        if result["significant_at_0_05"]
        else "not statistically significant"
    )

    return (
        f"{variable}: {trend}. "
        f"Slope: {result['slope']} {result['slope_unit']}. "
        f"p-value: {result['p_value']}. "
        f"The trend is {significance} at alpha=0.05. "
        f"Period: {result['start_date']} to {result['end_date']}. "
        f"Method: {result['method']}."
    )


async def get_location_results(request: LocationRequest) -> dict:
    mode = os.getenv("RESULTS_MODE", "demo").lower()

    if mode not in ("demo", "api"):
        raise ValueError("RESULTS_MODE must be demo or api")

    # DEMO: never invent measurements for a location.
    if mode == "demo":
        return {
            "location": request.location.model_dump(),
            "mode": "demo",
            "status": "no_location_specific_data",
            "results": {
                variable: {
                    "status": "unavailable",
                    "reason": (
                        "Location-specific analysis is unavailable "
                        "in demo mode."
                    ),
                }
                for variable in request.variables
            },
            "source": "DEMO_DATA",
            "is_demo": True,
            "notice": (
                "DEMO MODE - NOT REAL NASA FINDINGS. "
                "No location-specific trends can be concluded."
            ),
        }

    # REAL DATA: retrieve location-specific analysis
    # from Member 03's API.
    base_url = os.getenv(
        "RESULTS_API_BASE_URL", ""
    ).rstrip("/")

    if not base_url.startswith(("http://", "https://")):
        raise ValueError(
            "RESULTS_API_BASE_URL is missing or invalid"
        )

    api_token = os.getenv("RESULTS_API_TOKEN", "")

    headers = (
        {"Authorization": f"Bearer {api_token}"}
        if api_token
        else {}
    )

    results = {}

    async with httpx.AsyncClient(timeout=15.0) as client:
        for variable in request.variables:
            canonical = variable.replace("_", " ")

            try:
                response = await client.get(
                    f"{base_url}/locations/analysis",
                    params={
                        "latitude": request.location.latitude,
                        "longitude": request.location.longitude,
                        "variable": canonical,
                    },
                    headers=headers,
                )

                if response.status_code == 404:
                    results[variable] = {
                        "status": "unavailable",
                        "reason": "No data for this location",
                    }
                    continue

                response.raise_for_status()
                payload = response.json()

                if not isinstance(payload, dict):
                    raise ValueError("Invalid API response")

                # Confirm the returned result belongs
                # to the requested coordinates.
                coordinates = payload.get("location")

                if not isinstance(coordinates, dict):
                    raise ValueError(
                        "Missing location coordinates"
                    )

                for key, expected in (
                    ("latitude", request.location.latitude),
                    ("longitude", request.location.longitude),
                ):
                    actual = coordinates.get(key)

                    if (
                        isinstance(actual, bool)
                        or not isinstance(actual, (int, float))
                        or abs(actual - expected) > 0.0001
                    ):
                        raise ValueError(
                            "Location coordinates do not match"
                        )

                validated = validate_result(
                    payload,
                    canonical,
                    "location-analysis",
                    "EXTERNAL_ANALYSIS_API",
                )

                results[variable] = {
                    **validated,
                    "status": "available",
                    "trend": get_trend(validated["slope"]),
                    "interpretation": describe_result(
                        canonical, validated
                    ),
                }

            except (
                httpx.HTTPError,
                ValueError,
                TypeError,
            ):
                results[variable] = {
                    "status": "unavailable",
                    "reason": (
                        "Analysis unavailable or invalid"
                    ),
                }

    available_count = sum(
        result["status"] == "available"
        for result in results.values()
    )

    if available_count == len(results):
        status = "completed"
    elif available_count:
        status = "partial"
    else:
        status = "unavailable"

    return {
        "location": request.location.model_dump(),
        "mode": "api",
        "status": status,
        "results": results,
        "source": "EXTERNAL_ANALYSIS_API",
        "is_demo": False,
        "notice": (
            "Results are provided by an external analysis API. "
            "Dataset provenance and spatial resolution "
            "must be verified."
        ),
    }
