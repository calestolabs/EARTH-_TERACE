"""Strict demo/real investigation-result boundary. Demo values are fictional."""
import os
import httpx

DEMO = {
    "rainfall": {"slope": -1.2, "slope_unit": "mm/year", "p_value": 0.03},
    "temperature": {"slope": 0.025, "slope_unit": "°C/year", "p_value": 0.01},
    "soil moisture": {"slope": -0.001, "slope_unit": "dataset units/year", "p_value": 0.08},
}
ALIASES = {"rain": "rainfall", "precipitation": "rainfall", "temp": "temperature", "soil_moisture": "soil moisture", "soilmoisture": "soil moisture"}


def normalize_variable(value: str) -> str:
    value = value.strip().lower()
    return ALIASES.get(value, value)


def validate_result(
    data: dict,
    variable: str,
    investigation_id: str,
    source: str,
) -> dict:
    """Validate statistical results before presenting them to the AI."""
    import math
    from datetime import date

    if not isinstance(data, dict):
        raise ValueError("Result must be a JSON object")

    required = (
        "slope",
        "slope_unit",
        "p_value",
        "region",
        "start_date",
        "end_date",
        "method",
    )

    for field in required:
        if field not in data:
            raise ValueError(f"Missing required result field: {field}")

    slope = data["slope"]
    p = data["p_value"]

    if (
        isinstance(slope, bool)
        or not isinstance(slope, (int, float))
        or not math.isfinite(slope)
    ):
        raise ValueError("slope must be a finite number")

    if (
        isinstance(p, bool)
        or not isinstance(p, (int, float))
        or not math.isfinite(p)
        or not 0 <= p <= 1
    ):
        raise ValueError("p_value must be a finite number between 0 and 1")

    for field in ("slope_unit", "region", "start_date", "end_date", "method"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(f"{field} must be a nonempty string")

    try:
        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD format") from exc

    if start > end:
        raise ValueError("start_date must not be after end_date")

    return {
        "investigation_id": investigation_id,
        "variable": variable,
        "source": source,
        "is_demo": source == "DEMO_DATA",
        "slope": slope,
        "slope_unit": data["slope_unit"],
        "p_value": p,
        "region": data["region"],
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "method": data["method"],
        "significant_at_0_05": p < 0.05,
        "note": (
            "Fictional demonstration, not a NASA observation"
            if source == "DEMO_DATA"
            else "External analysis result; verify provenance with Member 03"
        ),
    }


def fetch_result(variable: str, investigation_id: str = "demo-south-asia") -> dict:
    variable = normalize_variable(variable)
    if variable not in DEMO:
        return {"error": "Unsupported variable", "supported": list(DEMO)}
    mode = os.getenv("RESULTS_MODE", "demo").lower()
    if mode == "demo":
        return validate_result({**DEMO[variable], "region": "Southern Asia", "start_date": "2000-01-01",
                                "end_date": "2024-12-31", "method": "Illustrative linear trend and illustrative p-value; not calculated"},
                               variable, investigation_id, "DEMO_DATA")
    if mode != "api":
        return {"error": "Invalid RESULTS_MODE; use demo or api"}
    base = os.getenv("RESULTS_API_BASE_URL", "").rstrip("/")
    if not base.startswith(("http://", "https://")):
        return {"error": "RESULTS_API_BASE_URL is not configured"}
    token = os.getenv("RESULTS_API_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        # httpx encodes variable query params and enforces a timeout.
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{base}/investigations/{investigation_id}/results",
                                  params={"variable": variable}, headers=headers)
            response.raise_for_status()
            payload = response.json()
        return validate_result(payload, variable, investigation_id, "EXTERNAL_ANALYSIS_API")
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        return {"error": "Analysis result unavailable or invalid", "detail": str(exc)}
