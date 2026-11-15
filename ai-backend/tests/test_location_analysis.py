
import pytest
from pydantic import ValidationError

from earthtrace_agent.location_analysis import (
    LocationRequest,
    get_location_results,
    get_trend,
)


def make_request():
    return LocationRequest(
        location={
            "name": "Colombo, Sri Lanka",
            "latitude": 6.9271,
            "longitude": 79.8612,
        }
    )


def test_default_variables():
    request = make_request()

    assert request.variables == [
        "temperature",
        "rainfall",
        "soil_moisture",
    ]


def test_trend_direction():
    assert get_trend(0.5) == "increasing"
    assert get_trend(-0.5) == "decreasing"
    assert get_trend(0) == "no_linear_change"


def test_invalid_coordinates():
    with pytest.raises(ValidationError):
        LocationRequest(
            location={
                "name": "Invalid location",
                "latitude": 120,
                "longitude": 79.8,
            }
        )


def test_duplicate_variables():
    with pytest.raises(ValidationError):
        LocationRequest(
            location={
                "name": "Colombo",
                "latitude": 6.9271,
                "longitude": 79.8612,
            },
            variables=["rainfall", "rainfall"],
        )


@pytest.mark.asyncio
async def test_demo_does_not_invent_results(monkeypatch):
    monkeypatch.setenv("RESULTS_MODE", "demo")

    report = await get_location_results(make_request())

    assert report["is_demo"] is True
    assert report["status"] == "no_location_specific_data"

    for result in report["results"].values():
        assert result["status"] == "unavailable"
        assert "slope" not in result
        assert "p_value" not in result
