"""Open-Meteo API client for fetching historical weather data."""

import os
import pandas as pd
import numpy as np
import openmeteo_requests
import requests_cache
from retry_requests import retry


def _get_client():
    """Create an Open-Meteo API client with caching and retry."""
    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)


def fetch_city_data(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    variables: list[str],
) -> pd.DataFrame:
    """Fetch hourly weather data for a single city from Open-Meteo."""
    client = _get_client()
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": variables,
    }
    responses = client.weather_api(
        "https://archive-api.open-meteo.com/v1/archive", params=params
    )
    response = responses[0]
    hourly = response.Hourly()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }
    for i, var in enumerate(variables):
        hourly_data[var] = hourly.Variables(i).ValuesAsNumpy()

    return pd.DataFrame(data=hourly_data)


def fetch_all_cities(
    cities: dict,
    start_date: str,
    end_date: str,
    variables: list[str],
    raw_dir: str,
) -> dict[str, pd.DataFrame]:
    """Fetch data for all cities. Cache as CSV."""
    os.makedirs(raw_dir, exist_ok=True)
    result = {}

    for city_name, coords in cities.items():
        cache_path = os.path.join(raw_dir, f"{city_name}.csv")
        if os.path.exists(cache_path):
            print(f"Loading cached data for {city_name}")
            result[city_name] = pd.read_csv(cache_path, parse_dates=["date"])
        else:
            print(f"Fetching data for {city_name}...")
            df = fetch_city_data(
                latitude=coords["latitude"],
                longitude=coords["longitude"],
                start_date=start_date,
                end_date=end_date,
                variables=variables,
            )
            df.to_csv(cache_path, index=False)
            result[city_name] = df

    return result
