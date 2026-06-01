# tests/test_preprocess.py
import pytest
import pandas as pd
import numpy as np
from data.preprocess import (
    add_lag_features,
    add_rolling_features,
    add_cyclical_features,
    add_derived_features,
    engineer_features,
    normalize_data,
    split_data,
)


@pytest.fixture
def sample_df():
    """Create a sample DataFrame mimicking raw weather data."""
    n = 24 * 365  # 1 year hourly
    dates = pd.date_range("2020-01-01", periods=n, freq="h")
    rng = np.random.RandomState(42)
    return pd.DataFrame({
        "date": dates,
        "temperature_2m": 20 + 10 * np.sin(np.arange(n) * 2 * np.pi / (24 * 365)) + rng.randn(n),
        "relative_humidity_2m": 50 + 20 * rng.randn(n),
        "wind_speed_10m": 5 + 2 * rng.randn(n),
        "pressure_msl": 1013 + 5 * rng.randn(n),
        "dew_point_2m": 15 + 8 * np.sin(np.arange(n) * 2 * np.pi / (24 * 365)) + rng.randn(n),
        "shortwave_radiation": np.clip(200 * np.sin(np.arange(n) * 2 * np.pi / 24), 0, None),
        "wind_gusts_10m": 8 + 3 * rng.randn(n),
    })


def test_add_lag_features(sample_df):
    result = add_lag_features(sample_df, variables=["temperature_2m"], lags=[1, 24])
    assert "temperature_2m_lag_1" in result.columns
    assert "temperature_2m_lag_24" in result.columns
    # Lag 1 should shift the value by 1 row
    assert result["temperature_2m_lag_1"].iloc[1] == sample_df["temperature_2m"].iloc[0]


def test_add_rolling_features(sample_df):
    result = add_rolling_features(sample_df, variables=["temperature_2m"], windows=[24])
    assert "temperature_2m_roll_mean_24" in result.columns
    assert "temperature_2m_roll_std_24" in result.columns


def test_add_cyclical_features(sample_df):
    result = add_cyclical_features(sample_df)
    assert "hour_sin" in result.columns
    assert "hour_cos" in result.columns
    assert "day_of_year_sin" in result.columns
    assert "day_of_year_cos" in result.columns


def test_add_derived_features(sample_df):
    result = add_derived_features(sample_df)
    assert "dew_point_depression" in result.columns
    expected = sample_df["temperature_2m"] - sample_df["dew_point_2m"]
    pd.testing.assert_series_equal(result["dew_point_depression"], expected, check_names=False)


def test_normalize_data():
    train = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})
    val = pd.DataFrame({"a": [4.0], "b": [40.0]})
    columns = ["a", "b"]
    train_norm, val_norm, scaler = normalize_data(train, val, columns)
    # Train mean should be ~0 after normalization
    assert abs(train_norm["a"].mean()) < 1e-10
    # Scaler should be fitted on train only
    assert scaler.mean_[0] == pytest.approx(2.0)


def test_split_data(sample_df):
    train, val, test = split_data(sample_df, train_years=0.5, val_years=0.3, test_years=0.2)
    total = len(train) + len(val) + len(test)
    assert total == len(sample_df)
    # Train dates should come before val dates
    assert train["date"].max() < val["date"].min()
    assert val["date"].max() < test["date"].min()
