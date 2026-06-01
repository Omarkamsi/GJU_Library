import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from data.fetch import fetch_city_data, fetch_all_cities


def test_fetch_city_data_returns_dataframe():
    """fetch_city_data should return a DataFrame with expected columns."""
    with patch("data.fetch.openmeteo_requests.Client") as mock_client:
        mock_response = MagicMock()
        mock_hourly = MagicMock()
        # Simulate 48 hours of data
        mock_hourly.Variables.return_value.ValuesAsNumpy.return_value = (
            __import__("numpy").random.rand(48)
        )
        mock_hourly.Time.return_value = 1704067200  # 2024-01-01 00:00
        mock_hourly.TimeEnd.return_value = 1704240000  # 2024-01-03 00:00
        mock_hourly.Interval.return_value = 3600
        mock_response.Hourly.return_value = mock_hourly
        mock_client.return_value.weather_api.return_value = [mock_response]

        df = fetch_city_data(
            latitude=31.95,
            longitude=35.93,
            start_date="2024-01-01",
            end_date="2024-01-02",
            variables=["temperature_2m", "relative_humidity_2m"],
        )
        assert isinstance(df, pd.DataFrame)
        assert "date" in df.columns
        assert "temperature_2m" in df.columns
        assert "relative_humidity_2m" in df.columns
        assert len(df) == 48


def test_fetch_all_cities_returns_dict():
    """fetch_all_cities should return a dict of city_name -> DataFrame."""
    cities = {
        "amman": {"latitude": 31.95, "longitude": 35.93},
    }
    with patch("data.fetch.fetch_city_data") as mock_fetch:
        mock_fetch.return_value = pd.DataFrame(
            {"date": pd.date_range("2024-01-01", periods=24, freq="h"),
             "temperature_2m": range(24)}
        )
        result = fetch_all_cities(
            cities=cities,
            start_date="2024-01-01",
            end_date="2024-01-01",
            variables=["temperature_2m"],
            raw_dir="/tmp/test_raw",
        )
        assert "amman" in result
        assert isinstance(result["amman"], pd.DataFrame)
