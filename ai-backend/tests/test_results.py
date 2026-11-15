
import pytest

from earthtrace_agent.results import (
    fetch_result,
    normalize_variable,
    validate_result,
)


def test_rainfall_demo(monkeypatch):
    monkeypatch.setenv("RESULTS_MODE", "demo")

    result = fetch_result("rainfall")

    assert result["source"] == "DEMO_DATA"
    assert result["is_demo"] is True
    assert result["slope"] == -1.2
    assert result["p_value"] == 0.03
    assert result["significant_at_0_05"] is True


def test_temperature_demo(monkeypatch):
    monkeypatch.setenv("RESULTS_MODE", "demo")

    result = fetch_result("temperature")

    assert result["slope"] == 0.025
    assert result["p_value"] == 0.01
    assert result["significant_at_0_05"] is True


def test_soil_moisture_demo(monkeypatch):
    monkeypatch.setenv("RESULTS_MODE", "demo")

    result = fetch_result("soil moisture")

    assert result["slope"] == -0.001
    assert result["p_value"] == 0.08
    assert result["significant_at_0_05"] is False


def test_variable_aliases():
    assert normalize_variable("rain") == "rainfall"
    assert normalize_variable("temp") == "temperature"
    assert normalize_variable("soil_moisture") == "soil moisture"


def test_unsupported_variable(monkeypatch):
    monkeypatch.setenv("RESULTS_MODE", "demo")

    result = fetch_result("humidity")

    assert result["error"] == "Unsupported variable"


def test_invalid_p_value():
    invalid_data = {
        "slope": 0.1,
        "slope_unit": "units/year",
        "p_value": 1.5,
        "region": "Southern Asia",
        "start_date": "2000-01-01",
        "end_date": "2024-12-31",
        "method": "Test method",
    }

    with pytest.raises(ValueError):
        validate_result(
            invalid_data,
            "temperature",
            "test-investigation",
            "DEMO_DATA",
        )

def test_invalid_results_mode(monkeypatch):
    monkeypatch.setenv("RESULTS_MODE", "invalid")

    result = fetch_result("rainfall")

    assert "error" in result


def test_nan_slope_rejected():
    data = {
        "slope": float("nan"),
        "slope_unit": "mm/year",
        "p_value": 0.03,
        "region": "Southern Asia",
        "start_date": "2000-01-01",
        "end_date": "2024-12-31",
        "method": "Linear trend",
    }

    with pytest.raises(ValueError):
        validate_result(
            data, "rainfall", "test-id", "DEMO_DATA"
        )


def test_invalid_date_range_rejected():
    data = {
        "slope": -1.2,
        "slope_unit": "mm/year",
        "p_value": 0.03,
        "region": "Southern Asia",
        "start_date": "2025-01-01",
        "end_date": "2000-01-01",
        "method": "Linear trend",
    }

    with pytest.raises(ValueError):
        validate_result(
            data, "rainfall", "test-id", "DEMO_DATA"
        )


