# tests/test_dataset.py
import pytest
import numpy as np
import pandas as pd
import torch
from data.dataset import WeatherDataset


@pytest.fixture
def sample_data():
    """Create normalized sample data with feature columns."""
    n = 500
    rng = np.random.RandomState(42)
    feature_cols = ["temperature_2m", "humidity", "wind", "hour_sin", "hour_cos",
                    "city_amman", "city_irbid", "city_aqaba"]
    target_cols = ["temperature_2m", "humidity", "wind"]
    data = pd.DataFrame(rng.randn(n, len(feature_cols)), columns=feature_cols)
    return data, feature_cols, target_cols


def test_dataset_length(sample_data):
    data, feature_cols, target_cols = sample_data
    ds = WeatherDataset(data, feature_cols, target_cols, window_size=168, horizons=[6, 24])
    # Length = total rows - window_size - max_horizon
    expected = len(data) - 168 - 24
    assert len(ds) == expected


def test_dataset_shapes(sample_data):
    data, feature_cols, target_cols = sample_data
    ds = WeatherDataset(data, feature_cols, target_cols, window_size=168, horizons=[6, 24])
    x, y = ds[0]
    assert x.shape == (168, len(feature_cols))  # (window, features)
    assert y.shape == (2, len(target_cols))  # (num_horizons, num_targets)


def test_dataset_values(sample_data):
    data, feature_cols, target_cols = sample_data
    ds = WeatherDataset(data, feature_cols, target_cols, window_size=10, horizons=[1, 3])
    x, y = ds[0]
    # x should be first 10 rows of feature data
    expected_x = data[feature_cols].iloc[:10].values
    np.testing.assert_array_almost_equal(x.numpy(), expected_x)
    # y[0] should be target at index 10+1-1=10, y[1] at index 10+3-1=12
    for i, h in enumerate([1, 3]):
        expected_y = data[target_cols].iloc[10 + h - 1].values
        np.testing.assert_array_almost_equal(y[i].numpy(), expected_y)
