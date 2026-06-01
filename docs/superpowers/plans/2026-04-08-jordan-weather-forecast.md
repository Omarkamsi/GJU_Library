# Jordan Weather Forecasting Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular weather forecasting pipeline comparing GRU and TFT models across multiple forecast horizons for three Jordanian cities.

**Architecture:** Config-driven pipeline with separate modules for data fetching (Open-Meteo API), preprocessing (feature engineering + normalization), model training (GRU baseline + TFT), and assessment (metrics + visualization). Experiment tracking via CSV logs and frozen configs.

**Tech Stack:** Python, PyTorch (CUDA), Open-Meteo API, pandas, numpy, scikit-learn, matplotlib, pyyaml

**Spec:** `docs/superpowers/specs/2026-04-08-jordan-weather-forecast-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `jordan-weather-forecast/config/default.yaml` | All hyperparameters, city coordinates, feature lists, training config |
| `jordan-weather-forecast/data/__init__.py` | Package init |
| `jordan-weather-forecast/data/fetch.py` | Open-Meteo API client, downloads and caches raw CSVs |
| `jordan-weather-forecast/data/preprocess.py` | Feature engineering, normalization, temporal splits |
| `jordan-weather-forecast/data/dataset.py` | PyTorch Dataset for sliding window sequences |
| `jordan-weather-forecast/models/__init__.py` | Package init |
| `jordan-weather-forecast/models/gru.py` | GRU forecasting model |
| `jordan-weather-forecast/models/tft.py` | Temporal Fusion Transformer model |
| `jordan-weather-forecast/training/__init__.py` | Package init |
| `jordan-weather-forecast/training/trainer.py` | Training loop, early stopping, checkpointing |
| `jordan-weather-forecast/training/assess.py` | Metrics computation, comparison tables, plots |
| `jordan-weather-forecast/main.py` | CLI entry point orchestrating the full pipeline |
| `jordan-weather-forecast/requirements.txt` | Python dependencies |
| `jordan-weather-forecast/tests/test_fetch.py` | Tests for data fetching |
| `jordan-weather-forecast/tests/test_preprocess.py` | Tests for feature engineering and splits |
| `jordan-weather-forecast/tests/test_dataset.py` | Tests for PyTorch dataset |
| `jordan-weather-forecast/tests/test_gru.py` | Tests for GRU model |
| `jordan-weather-forecast/tests/test_tft.py` | Tests for TFT model |
| `jordan-weather-forecast/tests/test_trainer.py` | Tests for training loop |
| `jordan-weather-forecast/tests/test_assess.py` | Tests for assessment metrics |

---

### Task 1: Project Scaffolding and Config

**Files:**
- Create: `jordan-weather-forecast/config/default.yaml`
- Create: `jordan-weather-forecast/requirements.txt`
- Create: `jordan-weather-forecast/data/__init__.py`
- Create: `jordan-weather-forecast/models/__init__.py`
- Create: `jordan-weather-forecast/training/__init__.py`
- Create: `jordan-weather-forecast/tests/__init__.py`

- [ ] **Step 1: Create project directory structure**

```bash
mkdir -p jordan-weather-forecast/{config,data,models,training,experiments/logs,notebooks,tests}
```

- [ ] **Step 2: Create requirements.txt**

```
torch>=2.0.0
openmeteo-requests>=1.2.0
requests-cache>=1.1.0
retry-requests>=2.0.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
pyyaml>=6.0
pytest>=7.4.0
```

- [ ] **Step 3: Create config/default.yaml**

```yaml
cities:
  amman:
    latitude: 31.95
    longitude: 35.93
  irbid:
    latitude: 32.56
    longitude: 35.85
  aqaba:
    latitude: 29.53
    longitude: 35.01

data:
  start_date: "2014-01-01"
  end_date: "2023-12-31"
  variables:
    - temperature_2m
    - relative_humidity_2m
    - wind_speed_10m
    - pressure_msl
    - dew_point_2m
    - shortwave_radiation
    - wind_gusts_10m
  targets:
    - temperature_2m
    - relative_humidity_2m
    - wind_speed_10m
  lag_hours: [1, 6, 24, 168]
  rolling_windows: [24, 168]
  raw_dir: "data/raw"
  processed_dir: "data/processed"

split:
  train_years: 7
  val_years: 2
  test_years: 1

model:
  window_size: 168
  horizons: [6, 12, 24, 48, 72]
  batch_size: 32

gru:
  hidden_size: 128
  num_layers: 2
  dropout: 0.3

tft:
  hidden_size: 64
  num_heads: 4
  dropout: 0.3
  quantiles: [0.1, 0.5, 0.9]

training:
  learning_rate: 0.001
  weight_decay: 0.0001
  scheduler_patience: 5
  early_stopping_patience: 10
  max_epochs: 100

experiments:
  log_dir: "experiments/logs"
```

- [ ] **Step 4: Create package __init__.py files**

Create empty `__init__.py` in `data/`, `models/`, `training/`, `tests/`.

- [ ] **Step 5: Install dependencies**

```bash
cd jordan-weather-forecast && pip install -r requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git init
git add .
git commit -m "feat: project scaffolding with config and dependencies"
```

---

### Task 2: Data Fetching Module

**Files:**
- Create: `jordan-weather-forecast/data/fetch.py`
- Create: `jordan-weather-forecast/tests/test_fetch.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fetch.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_fetch.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'data.fetch'`

- [ ] **Step 3: Write the implementation**

```python
# data/fetch.py
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_fetch.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add data/fetch.py tests/test_fetch.py
git commit -m "feat: data fetching module with Open-Meteo API client"
```

---

### Task 3: Preprocessing Module

**Files:**
- Create: `jordan-weather-forecast/data/preprocess.py`
- Create: `jordan-weather-forecast/tests/test_preprocess.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_preprocess.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# data/preprocess.py
"""Feature engineering, normalization, and temporal splits."""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def add_lag_features(
    df: pd.DataFrame, variables: list[str], lags: list[int]
) -> pd.DataFrame:
    """Add lagged versions of specified variables."""
    df = df.copy()
    for var in variables:
        for lag in lags:
            df[f"{var}_lag_{lag}"] = df[var].shift(lag)
    return df


def add_rolling_features(
    df: pd.DataFrame, variables: list[str], windows: list[int]
) -> pd.DataFrame:
    """Add rolling mean and std for specified variables."""
    df = df.copy()
    for var in variables:
        for w in windows:
            df[f"{var}_roll_mean_{w}"] = df[var].rolling(window=w, min_periods=1).mean()
            df[f"{var}_roll_std_{w}"] = df[var].rolling(window=w, min_periods=1).std()
    return df


def add_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add sin/cos encodings for hour-of-day and day-of-year."""
    df = df.copy()
    hour = df["date"].dt.hour
    day_of_year = df["date"].dt.dayofyear

    df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    df["day_of_year_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    df["day_of_year_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features like dew point depression."""
    df = df.copy()
    df["dew_point_depression"] = df["temperature_2m"] - df["dew_point_2m"]
    return df


def engineer_features(
    df: pd.DataFrame,
    variables: list[str],
    lags: list[int],
    rolling_windows: list[int],
) -> pd.DataFrame:
    """Apply all feature engineering steps and drop NaN rows."""
    df = add_lag_features(df, variables=variables, lags=lags)
    df = add_rolling_features(df, variables=variables, windows=rolling_windows)
    df = add_cyclical_features(df)
    df = add_derived_features(df)
    df = df.dropna().reset_index(drop=True)
    return df


def normalize_data(
    train: pd.DataFrame,
    val: pd.DataFrame,
    columns: list[str],
    test: pd.DataFrame = None,
) -> tuple:
    """Normalize using StandardScaler fit on train only.

    Returns (train_norm, val_norm, scaler) or
            (train_norm, val_norm, test_norm, scaler) if test is provided.
    """
    scaler = StandardScaler()
    train = train.copy()
    val = val.copy()

    train[columns] = scaler.fit_transform(train[columns])
    val[columns] = scaler.transform(val[columns])

    if test is not None:
        test = test.copy()
        test[columns] = scaler.transform(test[columns])
        return train, val, test, scaler

    return train, val, scaler


def split_data(
    df: pd.DataFrame, train_years: float, val_years: float, test_years: float
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split data temporally into train/val/test based on year proportions."""
    total = train_years + val_years + test_years
    n = len(df)
    train_end = int(n * train_years / total)
    val_end = int(n * (train_years + val_years) / total)

    train = df.iloc[:train_end].reset_index(drop=True)
    val = df.iloc[train_end:val_end].reset_index(drop=True)
    test = df.iloc[val_end:].reset_index(drop=True)

    return train, val, test
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_preprocess.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add data/preprocess.py tests/test_preprocess.py
git commit -m "feat: preprocessing module with feature engineering and normalization"
```

---

### Task 4: PyTorch Dataset

**Files:**
- Create: `jordan-weather-forecast/data/dataset.py`
- Create: `jordan-weather-forecast/tests/test_dataset.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_dataset.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# data/dataset.py
"""PyTorch Dataset for sliding window weather sequences."""

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


class WeatherDataset(Dataset):
    """Sliding window dataset for multi-horizon weather forecasting.

    Each sample: (x, y) where
        x: (window_size, num_features) -- input sequence
        y: (num_horizons, num_targets) -- target values at each horizon
    """

    def __init__(
        self,
        data: pd.DataFrame,
        feature_columns: list[str],
        target_columns: list[str],
        window_size: int,
        horizons: list[int],
    ):
        self.features = torch.tensor(
            data[feature_columns].values, dtype=torch.float32
        )
        self.targets = torch.tensor(
            data[target_columns].values, dtype=torch.float32
        )
        self.window_size = window_size
        self.horizons = horizons
        self.max_horizon = max(horizons)

    def __len__(self) -> int:
        return len(self.features) - self.window_size - self.max_horizon

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.features[idx : idx + self.window_size]
        y = torch.stack(
            [self.targets[idx + self.window_size + h - 1] for h in self.horizons]
        )
        return x, y
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_dataset.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add data/dataset.py tests/test_dataset.py
git commit -m "feat: PyTorch sliding window dataset for multi-horizon forecasting"
```

---

### Task 5: GRU Model

**Files:**
- Create: `jordan-weather-forecast/models/gru.py`
- Create: `jordan-weather-forecast/tests/test_gru.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gru.py
import pytest
import torch
from models.gru import GRUForecaster


def test_gru_output_shape():
    """GRU should output (batch, num_horizons, num_targets)."""
    model = GRUForecaster(
        input_size=15,
        hidden_size=128,
        num_layers=2,
        num_horizons=5,
        num_targets=3,
        dropout=0.3,
    )
    x = torch.randn(32, 168, 15)  # (batch, window, features)
    out = model(x)
    assert out.shape == (32, 5, 3)


def test_gru_single_sample():
    """GRU should work with batch size 1."""
    model = GRUForecaster(
        input_size=10,
        hidden_size=64,
        num_layers=2,
        num_horizons=3,
        num_targets=2,
        dropout=0.0,
    )
    model.set_to_inference_mode()
    x = torch.randn(1, 48, 10)
    out = model(x)
    assert out.shape == (1, 3, 2)
    assert not torch.isnan(out).any()


def test_gru_gradient_flow():
    """Gradients should flow through the model."""
    model = GRUForecaster(
        input_size=10, hidden_size=64, num_layers=2,
        num_horizons=3, num_targets=2, dropout=0.0,
    )
    x = torch.randn(4, 48, 10)
    y = torch.randn(4, 3, 2)
    out = model(x)
    loss = torch.nn.functional.mse_loss(out, y)
    loss.backward()
    for name, param in model.named_parameters():
        assert param.grad is not None, f"No gradient for {name}"
        assert not torch.isnan(param.grad).any(), f"NaN gradient for {name}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_gru.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# models/gru.py
"""GRU-based weather forecasting model."""

import torch
import torch.nn as nn


class GRUForecaster(nn.Module):
    """Multi-horizon weather forecaster using GRU.

    Takes a sequence of weather features and predicts target variables
    at multiple future horizons.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int,
        num_horizons: int,
        num_targets: int,
        dropout: float,
    ):
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Linear(hidden_size, num_horizons * num_targets)
        self.num_horizons = num_horizons
        self.num_targets = num_targets

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: (batch, window_size, input_size)
        Returns:
            (batch, num_horizons, num_targets)
        """
        _, h_n = self.gru(x)  # h_n: (num_layers, batch, hidden)
        h_last = h_n[-1]  # (batch, hidden)
        out = self.head(h_last)  # (batch, num_horizons * num_targets)
        return out.view(-1, self.num_horizons, self.num_targets)

    def set_to_inference_mode(self):
        """Switch model to inference mode (disables dropout)."""
        self.train(False)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_gru.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add models/gru.py tests/test_gru.py
git commit -m "feat: GRU forecasting model"
```

---

### Task 6: TFT Model

**Files:**
- Create: `jordan-weather-forecast/models/tft.py`
- Create: `jordan-weather-forecast/tests/test_tft.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tft.py
import pytest
import torch
from models.tft import TemporalFusionTransformer


def test_tft_output_shape():
    """TFT should output (batch, num_horizons, num_targets, num_quantiles)."""
    model = TemporalFusionTransformer(
        input_size=15,
        hidden_size=64,
        num_heads=4,
        num_horizons=5,
        num_targets=3,
        quantiles=[0.1, 0.5, 0.9],
        dropout=0.3,
    )
    x = torch.randn(16, 168, 15)
    out = model(x)
    assert out.shape == (16, 5, 3, 3)  # (batch, horizons, targets, quantiles)


def test_tft_single_sample():
    """TFT should work with batch size 1."""
    model = TemporalFusionTransformer(
        input_size=10,
        hidden_size=32,
        num_heads=4,
        num_horizons=3,
        num_targets=2,
        quantiles=[0.1, 0.5, 0.9],
        dropout=0.0,
    )
    model.set_to_inference_mode()
    x = torch.randn(1, 48, 10)
    out = model(x)
    assert out.shape == (1, 3, 2, 3)
    assert not torch.isnan(out).any()


def test_tft_gradient_flow():
    """Gradients should flow through the TFT."""
    model = TemporalFusionTransformer(
        input_size=10, hidden_size=32, num_heads=4,
        num_horizons=3, num_targets=2,
        quantiles=[0.1, 0.5, 0.9], dropout=0.0,
    )
    x = torch.randn(4, 48, 10)
    out = model(x)
    target = torch.randn(4, 3, 2)
    # Use median (quantile index 1) for MSE loss
    loss = torch.nn.functional.mse_loss(out[:, :, :, 1], target)
    loss.backward()
    for name, param in model.named_parameters():
        assert param.grad is not None, f"No gradient for {name}"


def test_tft_variable_importance():
    """TFT should expose variable importance weights."""
    model = TemporalFusionTransformer(
        input_size=10, hidden_size=32, num_heads=4,
        num_horizons=3, num_targets=2,
        quantiles=[0.1, 0.5, 0.9], dropout=0.0,
    )
    model.set_to_inference_mode()
    x = torch.randn(4, 48, 10)
    _ = model(x)
    importance = model.get_variable_importance()
    assert importance.shape == (10,)
    assert torch.allclose(importance.sum(), torch.tensor(1.0), atol=1e-5)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_tft.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# models/tft.py
"""Temporal Fusion Transformer for weather forecasting."""

import torch
import torch.nn as nn
import torch.nn.functional as F


class GatedResidualNetwork(nn.Module):
    """Gated Residual Network (GRN) block."""

    def __init__(self, input_size: int, hidden_size: int, output_size: int, dropout: float):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.elu = nn.ELU()
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(dropout)
        self.gate = nn.Linear(output_size, output_size)
        self.layer_norm = nn.LayerNorm(output_size)
        if input_size != output_size:
            self.skip = nn.Linear(input_size, output_size)
        else:
            self.skip = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x if self.skip is None else self.skip(x)
        h = self.elu(self.fc1(x))
        h = self.dropout(self.fc2(h))
        gate = torch.sigmoid(self.gate(h))
        return self.layer_norm(gate * h + residual)


class VariableSelectionNetwork(nn.Module):
    """Variable Selection Network -- learns which input features matter most."""

    def __init__(self, input_size: int, hidden_size: int, dropout: float):
        super().__init__()
        self.input_size = input_size
        self.flattened_grn = GatedResidualNetwork(input_size, hidden_size, input_size, dropout)
        self.softmax = nn.Softmax(dim=-1)
        self.per_variable_grn = GatedResidualNetwork(1, hidden_size, hidden_size, dropout)
        self.hidden_size = hidden_size
        self._importance_weights = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, input_size)
        Returns:
            (batch, seq_len, hidden_size)
        """
        # Compute variable selection weights
        flat = x.mean(dim=1)  # (batch, input_size)
        weights = self.softmax(self.flattened_grn(flat))  # (batch, input_size)
        self._importance_weights = weights.detach()

        # Process each variable through its own GRN
        var_outputs = []
        for i in range(self.input_size):
            var_input = x[:, :, i : i + 1]  # (batch, seq_len, 1)
            b, s, _ = var_input.shape
            var_out = self.per_variable_grn(var_input.reshape(b * s, 1))  # (b*s, hidden)
            var_outputs.append(var_out.reshape(b, s, self.hidden_size))

        # Stack and weight
        stacked = torch.stack(var_outputs, dim=-1)  # (batch, seq, hidden, input_size)
        weights_expanded = weights.unsqueeze(1).unsqueeze(1)  # (batch, 1, 1, input_size)
        combined = (stacked * weights_expanded).sum(dim=-1)  # (batch, seq, hidden)
        return combined

    def get_importance(self) -> torch.Tensor:
        """Return mean variable importance weights from last forward pass."""
        if self._importance_weights is None:
            raise RuntimeError("Must run forward pass first")
        return self._importance_weights.mean(dim=0)


class TemporalFusionTransformer(nn.Module):
    """Simplified TFT for multi-horizon weather forecasting with quantile output."""

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_heads: int,
        num_horizons: int,
        num_targets: int,
        quantiles: list[float],
        dropout: float,
    ):
        super().__init__()
        self.num_horizons = num_horizons
        self.num_targets = num_targets
        self.quantiles = quantiles

        # Variable selection
        self.vsn = VariableSelectionNetwork(input_size, hidden_size, dropout)

        # Temporal processing with LSTM (as in original TFT paper)
        self.lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            dropout=0.0,
        )

        # Post-LSTM GRN
        self.post_lstm_grn = GatedResidualNetwork(hidden_size, hidden_size, hidden_size, dropout)

        # Multi-head attention
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size, num_heads=num_heads, dropout=dropout, batch_first=True,
        )
        self.attn_layer_norm = nn.LayerNorm(hidden_size)

        # Output GRN and head
        self.output_grn = GatedResidualNetwork(hidden_size, hidden_size, hidden_size, dropout)
        self.output_head = nn.Linear(
            hidden_size, num_horizons * num_targets * len(quantiles)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, window_size, input_size)
        Returns:
            (batch, num_horizons, num_targets, num_quantiles)
        """
        # Variable selection
        selected = self.vsn(x)  # (batch, seq, hidden)

        # Temporal processing
        lstm_out, _ = self.lstm(selected)  # (batch, seq, hidden)
        temporal = self.post_lstm_grn(lstm_out)  # (batch, seq, hidden)

        # Self-attention
        attn_out, _ = self.attention(temporal, temporal, temporal)
        attn_out = self.attn_layer_norm(attn_out + temporal)  # residual

        # Use last timestep for prediction
        last = attn_out[:, -1, :]  # (batch, hidden)
        out = self.output_grn(last)  # (batch, hidden)
        out = self.output_head(out)  # (batch, horizons * targets * quantiles)

        return out.view(
            -1, self.num_horizons, self.num_targets, len(self.quantiles)
        )

    def get_variable_importance(self) -> torch.Tensor:
        """Return variable importance weights from last forward pass."""
        return self.vsn.get_importance()

    def set_to_inference_mode(self):
        """Switch model to inference mode (disables dropout)."""
        self.train(False)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_tft.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add models/tft.py tests/test_tft.py
git commit -m "feat: Temporal Fusion Transformer model with variable selection"
```

---

### Task 7: Training Loop

**Files:**
- Create: `jordan-weather-forecast/training/trainer.py`
- Create: `jordan-weather-forecast/tests/test_trainer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_trainer.py
import pytest
import os
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from training.trainer import Trainer, QuantileLoss


@pytest.fixture
def dummy_model():
    """Simple linear model for testing the training loop."""
    class Wrapper(nn.Module):
        def __init__(self):
            super().__init__()
            self.inner = nn.Linear(10, 5 * 3)
        def forward(self, x):
            # x: (batch, seq, features) -> take last step
            out = self.inner(x[:, -1, :])
            return out.view(-1, 5, 3)
    return Wrapper()


@pytest.fixture
def dummy_loaders():
    """Create small dummy data loaders."""
    x = torch.randn(100, 20, 10)  # (samples, seq, features)
    y = torch.randn(100, 5, 3)     # (samples, horizons, targets)
    ds = TensorDataset(x, y)
    train_loader = DataLoader(ds, batch_size=16, shuffle=True)
    val_loader = DataLoader(ds, batch_size=16)
    return train_loader, val_loader


@pytest.fixture
def log_dir(tmp_path):
    return str(tmp_path / "test_logs")


def test_trainer_runs_one_epoch(dummy_model, dummy_loaders, log_dir):
    train_loader, val_loader = dummy_loaders
    trainer = Trainer(
        model=dummy_model,
        train_loader=train_loader,
        val_loader=val_loader,
        learning_rate=0.001,
        weight_decay=0.0001,
        scheduler_patience=5,
        early_stopping_patience=10,
        max_epochs=1,
        log_dir=log_dir,
        device="cpu",
    )
    trainer.train()
    assert os.path.exists(os.path.join(log_dir, "metrics.csv"))
    assert os.path.exists(os.path.join(log_dir, "model_best.pt"))


def test_trainer_early_stopping(dummy_model, dummy_loaders, log_dir):
    train_loader, val_loader = dummy_loaders
    trainer = Trainer(
        model=dummy_model,
        train_loader=train_loader,
        val_loader=val_loader,
        learning_rate=0.001,
        weight_decay=0.0001,
        scheduler_patience=2,
        early_stopping_patience=3,
        max_epochs=1000,
        log_dir=log_dir,
        device="cpu",
    )
    trainer.train()
    # Should stop well before 1000 epochs
    assert trainer.current_epoch < 1000


def test_quantile_loss():
    pred = torch.tensor([[[1.0, 2.0, 3.0]]])  # (1, 1, 3 quantiles)
    target = torch.tensor([[2.0]])              # (1, 1)
    loss_fn = QuantileLoss(quantiles=[0.1, 0.5, 0.9])
    loss = loss_fn(pred, target)
    assert loss.item() > 0
    assert not torch.isnan(loss)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_trainer.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# training/trainer.py
"""Training loop with early stopping, checkpointing, and experiment logging."""

import os
import csv
import time
import yaml
import torch
import torch.nn as nn
from torch.utils.data import DataLoader


class QuantileLoss(nn.Module):
    """Quantile loss for probabilistic forecasting."""

    def __init__(self, quantiles: list[float]):
        super().__init__()
        self.quantiles = quantiles

    def forward(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            predictions: (..., num_quantiles)
            targets: (...) matching predictions shape minus last dim
        """
        if targets.dim() < predictions.dim():
            targets = targets.unsqueeze(-1)

        losses = []
        for i, q in enumerate(self.quantiles):
            pred_q = predictions[..., i]
            errors = targets.squeeze(-1) - pred_q
            losses.append(torch.max(q * errors, (q - 1) * errors))

        return torch.stack(losses).mean()


class Trainer:
    """Handles model training with early stopping and experiment logging."""

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        learning_rate: float,
        weight_decay: float,
        scheduler_patience: int,
        early_stopping_patience: int,
        max_epochs: int,
        log_dir: str,
        device: str = "cuda",
        loss_fn: nn.Module = None,
        config: dict = None,
    ):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.max_epochs = max_epochs
        self.device = device
        self.log_dir = log_dir
        self.current_epoch = 0

        self.loss_fn = loss_fn or nn.MSELoss()
        self.optimizer = torch.optim.AdamW(
            model.parameters(), lr=learning_rate, weight_decay=weight_decay
        )
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", patience=scheduler_patience, factor=0.5
        )

        self.early_stopping_patience = early_stopping_patience
        self.best_val_loss = float("inf")
        self.patience_counter = 0

        os.makedirs(log_dir, exist_ok=True)
        if config:
            with open(os.path.join(log_dir, "config.yaml"), "w") as f:
                yaml.dump(config, f)

        self.metrics_path = os.path.join(log_dir, "metrics.csv")
        with open(self.metrics_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["epoch", "train_loss", "val_loss", "lr", "time_s"])

    def _train_epoch(self) -> float:
        self.model.train()
        total_loss = 0.0
        for x, y in self.train_loader:
            x, y = x.to(self.device), y.to(self.device)
            self.optimizer.zero_grad()
            pred = self.model(x)
            loss = self.loss_fn(pred, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            total_loss += loss.item() * x.size(0)
        return total_loss / len(self.train_loader.dataset)

    @torch.no_grad()
    def _validate_epoch(self) -> float:
        self.model.train(False)
        total_loss = 0.0
        for x, y in self.val_loader:
            x, y = x.to(self.device), y.to(self.device)
            pred = self.model(x)
            loss = self.loss_fn(pred, y)
            total_loss += loss.item() * x.size(0)
        return total_loss / len(self.val_loader.dataset)

    def train(self) -> None:
        """Run training loop with early stopping."""
        for epoch in range(self.max_epochs):
            self.current_epoch = epoch + 1
            start = time.time()

            train_loss = self._train_epoch()
            val_loss = self._validate_epoch()
            elapsed = time.time() - start

            lr = self.optimizer.param_groups[0]["lr"]
            self.scheduler.step(val_loss)

            # Log metrics
            with open(self.metrics_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([epoch + 1, f"{train_loss:.6f}", f"{val_loss:.6f}",
                                 f"{lr:.2e}", f"{elapsed:.1f}"])

            print(f"Epoch {epoch+1}/{self.max_epochs} | "
                  f"Train: {train_loss:.6f} | Val: {val_loss:.6f} | "
                  f"LR: {lr:.2e} | {elapsed:.1f}s")

            # Checkpointing
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.patience_counter = 0
                torch.save(
                    self.model.state_dict(),
                    os.path.join(self.log_dir, "model_best.pt"),
                )
            else:
                self.patience_counter += 1

            if self.patience_counter >= self.early_stopping_patience:
                print(f"Early stopping at epoch {epoch + 1}")
                break

    def load_best(self) -> None:
        """Load the best checkpoint."""
        path = os.path.join(self.log_dir, "model_best.pt")
        self.model.load_state_dict(torch.load(path, map_location=self.device))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_trainer.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add training/trainer.py tests/test_trainer.py
git commit -m "feat: training loop with early stopping and experiment logging"
```

---

### Task 8: Assessment Module

**Files:**
- Create: `jordan-weather-forecast/training/assess.py`
- Create: `jordan-weather-forecast/tests/test_assess.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_assess.py
import pytest
import os
import numpy as np
import pandas as pd
from training.assess import (
    compute_metrics,
    generate_comparison_table,
)


def test_compute_metrics():
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.2, 2.8, 4.1, 5.3])
    metrics = compute_metrics(y_true, y_pred)
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert "mape" in metrics
    assert metrics["mae"] < 0.5
    assert metrics["r2"] > 0.9


def test_compute_metrics_perfect():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    metrics = compute_metrics(y_true, y_pred)
    assert metrics["mae"] == pytest.approx(0.0)
    assert metrics["r2"] == pytest.approx(1.0)


def test_generate_comparison_table(tmp_path):
    results = {
        "gru": {
            "amman": {
                "temperature_2m": {
                    6: {"mae": 0.5, "rmse": 0.7, "r2": 0.95, "mape": 2.1},
                    24: {"mae": 1.0, "rmse": 1.3, "r2": 0.90, "mape": 4.5},
                },
            },
        },
        "tft": {
            "amman": {
                "temperature_2m": {
                    6: {"mae": 0.4, "rmse": 0.6, "r2": 0.96, "mape": 1.8},
                    24: {"mae": 0.9, "rmse": 1.1, "r2": 0.92, "mape": 3.9},
                },
            },
        },
    }
    output_path = str(tmp_path / "comparison.csv")
    generate_comparison_table(results, output_path)
    assert os.path.exists(output_path)
    df = pd.read_csv(output_path)
    assert len(df) > 0
    assert "model" in df.columns
    assert "mae" in df.columns
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_assess.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# training/assess.py
"""Assessment metrics, comparison tables, and visualizations."""

import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute MAE, RMSE, R-squared, and MAPE."""
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    mask = np.abs(y_true) > 1e-8
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.any() else 0.0
    return {"mae": float(mae), "rmse": float(rmse), "r2": float(r2), "mape": float(mape)}


@torch.no_grad()
def run_model_assessment(
    model: nn.Module,
    test_loader: DataLoader,
    target_columns: list[str],
    horizons: list[int],
    city_names: list[str],
    city_indices: dict[str, tuple[int, int]],
    scaler,
    target_col_indices: list[int],
    device: str = "cuda",
    is_quantile: bool = False,
) -> dict[str, dict[str, dict[int, dict]]]:
    """Run model assessment and return nested metrics dict.

    Returns: {city: {target: {horizon: {mae, rmse, r2, mape}}}}
    """
    model.train(False)
    all_preds = []
    all_targets = []

    for x, y in test_loader:
        x = x.to(device)
        pred = model(x).cpu()
        if is_quantile:
            pred = pred[:, :, :, 1]  # Take median (50th percentile)
        all_preds.append(pred)
        all_targets.append(y)

    preds = torch.cat(all_preds, dim=0).numpy()   # (N, horizons, targets)
    targets = torch.cat(all_targets, dim=0).numpy()

    results = {}
    for city in city_names:
        results[city] = {}
        for t_idx, target in enumerate(target_columns):
            results[city][target] = {}
            for h_idx, horizon in enumerate(horizons):
                p = preds[:, h_idx, t_idx]
                t = targets[:, h_idx, t_idx]
                results[city][target][horizon] = compute_metrics(t, p)

    return results


def generate_comparison_table(
    results: dict[str, dict], output_path: str
) -> pd.DataFrame:
    """Generate and save a comparison CSV from nested results dicts.

    Args:
        results: {model_name: {city: {target: {horizon: {metrics}}}}}
    """
    rows = []
    for model_name, cities in results.items():
        for city, targets in cities.items():
            for target, horizons in targets.items():
                for horizon, metrics in horizons.items():
                    rows.append({
                        "model": model_name,
                        "city": city,
                        "target": target,
                        "horizon_h": horizon,
                        **metrics,
                    })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nComparison table saved to {output_path}")
    print(df.to_string(index=False))
    return df


def plot_degradation_curves(
    results: dict, horizons: list[int], output_dir: str
) -> None:
    """Plot MAE vs forecast horizon for each model and target."""
    os.makedirs(output_dir, exist_ok=True)

    first_model = next(iter(results))
    first_city = next(iter(results[first_model]))
    targets = list(results[first_model][first_city].keys())

    for target in targets:
        fig, ax = plt.subplots(figsize=(10, 6))
        for model_name in results:
            maes = []
            for h in horizons:
                city_maes = [
                    results[model_name][city][target][h]["mae"]
                    for city in results[model_name]
                ]
                maes.append(np.mean(city_maes))
            ax.plot(horizons, maes, marker="o", label=model_name.upper())

        ax.set_xlabel("Forecast Horizon (hours)")
        ax.set_ylabel("MAE")
        ax.set_title(f"Forecast Degradation: {target}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.savefig(os.path.join(output_dir, f"degradation_{target}.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)

    print(f"Degradation curves saved to {output_dir}")


def plot_predictions(
    model: nn.Module,
    test_loader: DataLoader,
    target_columns: list[str],
    horizons: list[int],
    output_dir: str,
    device: str = "cuda",
    is_quantile: bool = False,
    num_samples: int = 336,
) -> None:
    """Plot actual vs predicted for a sample window."""
    os.makedirs(output_dir, exist_ok=True)
    model.train(False)

    all_preds = []
    all_targets = []
    with torch.no_grad():
        for x, y in test_loader:
            pred = model(x.to(device)).cpu()
            if is_quantile:
                pred = pred[:, :, :, 1]
            all_preds.append(pred)
            all_targets.append(y)
            if sum(p.size(0) for p in all_preds) >= num_samples:
                break

    preds = torch.cat(all_preds, dim=0)[:num_samples].numpy()
    targets = torch.cat(all_targets, dim=0)[:num_samples].numpy()

    h_idx = horizons.index(24) if 24 in horizons else 0
    for t_idx, target in enumerate(target_columns):
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(targets[:, h_idx, t_idx], label="Actual", alpha=0.8)
        ax.plot(preds[:, h_idx, t_idx], label="Predicted", alpha=0.8)
        ax.set_xlabel("Time Step")
        ax.set_ylabel(target)
        ax.set_title(f"Actual vs Predicted: {target} (24h horizon)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.savefig(os.path.join(output_dir, f"predictions_{target}.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)

    print(f"Prediction plots saved to {output_dir}")


def plot_loss_curves(metrics_csv: str, output_path: str) -> None:
    """Plot training vs validation loss from metrics CSV."""
    df = pd.read_csv(metrics_csv)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df["epoch"], df["train_loss"], label="Train Loss")
    ax.plot(df["epoch"], df["val_loss"], label="Validation Loss")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title("Training vs Validation Loss")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_feature_importance(importance: np.ndarray, feature_names: list[str], output_path: str) -> None:
    """Plot feature importance bar chart from TFT variable selection."""
    sorted_idx = np.argsort(importance)[::-1]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(range(len(importance)), importance[sorted_idx])
    ax.set_xticks(range(len(importance)))
    ax.set_xticklabels([feature_names[i] for i in sorted_idx], rotation=45, ha="right")
    ax.set_ylabel("Importance Weight")
    ax.set_title("TFT Variable Importance")
    ax.grid(True, alpha=0.3, axis="y")
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_assess.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add training/assess.py tests/test_assess.py
git commit -m "feat: assessment module with metrics, comparison tables, and plots"
```

---

### Task 9: Main Entry Point

**Files:**
- Create: `jordan-weather-forecast/main.py`

- [ ] **Step 1: Write the implementation**

```python
# main.py
"""CLI entry point for the Jordan weather forecasting pipeline."""

import argparse
import os
import yaml
import torch
import numpy as np
import pandas as pd
from torch.utils.data import DataLoader

from data.fetch import fetch_all_cities
from data.preprocess import engineer_features, normalize_data, split_data
from data.dataset import WeatherDataset
from models.gru import GRUForecaster
from models.tft import TemporalFusionTransformer
from training.trainer import Trainer, QuantileLoss
from training.assess import (
    run_model_assessment,
    generate_comparison_table,
    plot_degradation_curves,
    plot_predictions,
    plot_loss_curves,
    plot_feature_importance,
)


def load_config(path: str = "config/default.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def prepare_data(config: dict) -> tuple:
    """Fetch, engineer features, normalize, and create data loaders."""
    data_cfg = config["data"]
    split_cfg = config["split"]

    # Fetch data
    city_dfs = fetch_all_cities(
        cities=config["cities"],
        start_date=data_cfg["start_date"],
        end_date=data_cfg["end_date"],
        variables=data_cfg["variables"],
        raw_dir=data_cfg["raw_dir"],
    )

    # Combine all cities with city labels
    all_dfs = []
    for city_name, df in city_dfs.items():
        df = df.copy()
        for c in config["cities"]:
            df[f"city_{c}"] = 1.0 if c == city_name else 0.0
        all_dfs.append(df)
    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.sort_values("date").reset_index(drop=True)

    # Feature engineering
    combined = engineer_features(
        combined,
        variables=data_cfg["variables"],
        lags=data_cfg["lag_hours"],
        rolling_windows=data_cfg["rolling_windows"],
    )

    # Split
    train, val, test = split_data(
        combined,
        train_years=split_cfg["train_years"],
        val_years=split_cfg["val_years"],
        test_years=split_cfg["test_years"],
    )

    # Determine feature columns (everything except date)
    exclude = {"date"}
    feature_columns = [c for c in train.columns if c not in exclude]
    numeric_columns = [
        c for c in feature_columns
        if train[c].dtype in [np.float64, np.float32, "float64", "float32", np.int64]
    ]
    target_columns = data_cfg["targets"]

    # Normalize
    train, val, test, scaler = normalize_data(train, val, numeric_columns, test=test)

    # Create datasets
    model_cfg = config["model"]
    train_ds = WeatherDataset(
        train, feature_columns, target_columns,
        model_cfg["window_size"], model_cfg["horizons"],
    )
    val_ds = WeatherDataset(
        val, feature_columns, target_columns,
        model_cfg["window_size"], model_cfg["horizons"],
    )
    test_ds = WeatherDataset(
        test, feature_columns, target_columns,
        model_cfg["window_size"], model_cfg["horizons"],
    )

    batch_size = model_cfg["batch_size"]
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=2)

    return train_loader, val_loader, test_loader, feature_columns, target_columns, scaler


def train_gru(config, train_loader, val_loader, feature_columns, device):
    """Build and train GRU model."""
    gru_cfg = config["gru"]
    model_cfg = config["model"]
    train_cfg = config["training"]
    log_dir = os.path.join(config["experiments"]["log_dir"], "gru_latest")

    model = GRUForecaster(
        input_size=len(feature_columns),
        hidden_size=gru_cfg["hidden_size"],
        num_layers=gru_cfg["num_layers"],
        num_horizons=len(model_cfg["horizons"]),
        num_targets=len(config["data"]["targets"]),
        dropout=gru_cfg["dropout"],
    )

    trainer = Trainer(
        model=model, train_loader=train_loader, val_loader=val_loader,
        learning_rate=train_cfg["learning_rate"],
        weight_decay=train_cfg["weight_decay"],
        scheduler_patience=train_cfg["scheduler_patience"],
        early_stopping_patience=train_cfg["early_stopping_patience"],
        max_epochs=train_cfg["max_epochs"],
        log_dir=log_dir, device=device, config=config,
    )

    print("\n" + "=" * 60)
    print("Training GRU Model")
    print("=" * 60)
    trainer.train()
    trainer.load_best()
    plot_loss_curves(
        os.path.join(log_dir, "metrics.csv"),
        os.path.join(log_dir, "loss_curves.png"),
    )
    return model


def train_tft(config, train_loader, val_loader, feature_columns, device):
    """Build and train TFT model."""
    tft_cfg = config["tft"]
    model_cfg = config["model"]
    train_cfg = config["training"]
    log_dir = os.path.join(config["experiments"]["log_dir"], "tft_latest")

    model = TemporalFusionTransformer(
        input_size=len(feature_columns),
        hidden_size=tft_cfg["hidden_size"],
        num_heads=tft_cfg["num_heads"],
        num_horizons=len(model_cfg["horizons"]),
        num_targets=len(config["data"]["targets"]),
        quantiles=tft_cfg["quantiles"],
        dropout=tft_cfg["dropout"],
    )

    loss_fn = QuantileLoss(quantiles=tft_cfg["quantiles"])

    trainer = Trainer(
        model=model, train_loader=train_loader, val_loader=val_loader,
        learning_rate=train_cfg["learning_rate"],
        weight_decay=train_cfg["weight_decay"],
        scheduler_patience=train_cfg["scheduler_patience"],
        early_stopping_patience=train_cfg["early_stopping_patience"],
        max_epochs=train_cfg["max_epochs"],
        log_dir=log_dir, device=device, loss_fn=loss_fn, config=config,
    )

    print("\n" + "=" * 60)
    print("Training TFT Model")
    print("=" * 60)
    trainer.train()
    trainer.load_best()
    plot_loss_curves(
        os.path.join(log_dir, "metrics.csv"),
        os.path.join(log_dir, "loss_curves.png"),
    )

    # Feature importance
    model.train(False)
    with torch.no_grad():
        for x, _ in val_loader:
            model(x.to(device))
            break
    importance = model.get_variable_importance().numpy()
    plot_feature_importance(
        importance, feature_columns,
        os.path.join(log_dir, "feature_importance.png"),
    )

    return model


def run_full_assessment(
    config, gru_model, tft_model, test_loader,
    feature_columns, target_columns, scaler, device,
):
    """Assess both models and generate comparison outputs."""
    model_cfg = config["model"]
    horizons = model_cfg["horizons"]
    city_names = list(config["cities"].keys())
    city_indices = {city: (0, -1) for city in city_names}
    target_col_indices = [feature_columns.index(t) for t in target_columns]
    log_dir = config["experiments"]["log_dir"]

    all_results = {}

    if gru_model is not None:
        print("\n" + "=" * 60)
        print("Assessing GRU Model")
        print("=" * 60)
        gru_results = run_model_assessment(
            gru_model, test_loader, target_columns, horizons,
            city_names, city_indices, scaler, target_col_indices, device,
        )
        all_results["gru"] = gru_results
        plot_predictions(
            gru_model, test_loader, target_columns, horizons,
            os.path.join(log_dir, "gru_latest", "plots"), device,
        )

    if tft_model is not None:
        print("\n" + "=" * 60)
        print("Assessing TFT Model")
        print("=" * 60)
        tft_results = run_model_assessment(
            tft_model, test_loader, target_columns, horizons,
            city_names, city_indices, scaler, target_col_indices, device,
            is_quantile=True,
        )
        all_results["tft"] = tft_results
        plot_predictions(
            tft_model, test_loader, target_columns, horizons,
            os.path.join(log_dir, "tft_latest", "plots"), device,
            is_quantile=True,
        )

    if all_results:
        comparison_path = os.path.join(log_dir, "comparison.csv")
        generate_comparison_table(all_results, comparison_path)
        plot_degradation_curves(all_results, horizons, os.path.join(log_dir, "plots"))


def main():
    parser = argparse.ArgumentParser(description="Jordan Weather Forecasting Pipeline")
    parser.add_argument("--config", default="config/default.yaml", help="Config file path")
    parser.add_argument("--fetch-only", action="store_true", help="Only fetch data")
    parser.add_argument("--model", choices=["gru", "tft"], help="Train only this model")
    parser.add_argument("--assess-only", action="store_true", help="Only assess saved models")
    args = parser.parse_args()

    config = load_config(args.config)
    device = get_device()
    print(f"Using device: {device}")

    if args.fetch_only:
        fetch_all_cities(
            cities=config["cities"],
            start_date=config["data"]["start_date"],
            end_date=config["data"]["end_date"],
            variables=config["data"]["variables"],
            raw_dir=config["data"]["raw_dir"],
        )
        print("Data fetching complete.")
        return

    # Prepare data
    train_loader, val_loader, test_loader, feature_columns, target_columns, scaler = (
        prepare_data(config)
    )
    print(f"Features: {len(feature_columns)}, Targets: {len(target_columns)}")

    gru_model = None
    tft_model = None

    if not args.assess_only:
        if args.model is None or args.model == "gru":
            gru_model = train_gru(config, train_loader, val_loader, feature_columns, device)
        if args.model is None or args.model == "tft":
            tft_model = train_tft(config, train_loader, val_loader, feature_columns, device)
    else:
        # Load saved models
        log_dir = config["experiments"]["log_dir"]
        model_cfg = config["model"]
        num_targets = len(config["data"]["targets"])
        num_horizons = len(model_cfg["horizons"])

        gru_path = os.path.join(log_dir, "gru_latest", "model_best.pt")
        if os.path.exists(gru_path):
            gru_model = GRUForecaster(
                len(feature_columns), config["gru"]["hidden_size"],
                config["gru"]["num_layers"], num_horizons, num_targets,
                config["gru"]["dropout"],
            ).to(device)
            gru_model.load_state_dict(torch.load(gru_path, map_location=device))

        tft_path = os.path.join(log_dir, "tft_latest", "model_best.pt")
        if os.path.exists(tft_path):
            tft_model = TemporalFusionTransformer(
                len(feature_columns), config["tft"]["hidden_size"],
                config["tft"]["num_heads"], num_horizons, num_targets,
                config["tft"]["quantiles"], config["tft"]["dropout"],
            ).to(device)
            tft_model.load_state_dict(torch.load(tft_path, map_location=device))

    # Assess
    run_full_assessment(
        config, gru_model, tft_model, test_loader,
        feature_columns, target_columns, scaler, device,
    )

    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the CLI help works**

```bash
cd jordan-weather-forecast && python main.py --help
```

Expected: Shows help with `--fetch-only`, `--model`, `--assess-only` options

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: main CLI entry point orchestrating full pipeline"
```

---

### Task 10: Integration Test

**Files:**
- Create: `jordan-weather-forecast/tests/test_integration.py`

- [ ] **Step 1: Write the integration test**

```python
# tests/test_integration.py
"""End-to-end integration test with synthetic data."""

import pytest
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from data.preprocess import engineer_features, normalize_data, split_data
from data.dataset import WeatherDataset
from models.gru import GRUForecaster
from models.tft import TemporalFusionTransformer
from training.trainer import Trainer, QuantileLoss
from training.assess import compute_metrics


def _make_synthetic_data(n_hours: int = 24 * 365 * 2) -> pd.DataFrame:
    """Generate 2 years of synthetic hourly weather data."""
    rng = np.random.RandomState(42)
    dates = pd.date_range("2020-01-01", periods=n_hours, freq="h")
    t = np.arange(n_hours)
    return pd.DataFrame({
        "date": dates,
        "temperature_2m": 20 + 10 * np.sin(2 * np.pi * t / (24 * 365)) + rng.randn(n_hours) * 2,
        "relative_humidity_2m": 50 + 15 * np.sin(2 * np.pi * t / (24 * 365) + 1) + rng.randn(n_hours) * 5,
        "wind_speed_10m": 5 + 2 * np.sin(2 * np.pi * t / 24) + rng.randn(n_hours),
        "pressure_msl": 1013 + 5 * rng.randn(n_hours),
        "dew_point_2m": 15 + 8 * np.sin(2 * np.pi * t / (24 * 365)) + rng.randn(n_hours),
        "shortwave_radiation": np.clip(300 * np.sin(2 * np.pi * t / 24 - np.pi / 2), 0, None),
        "wind_gusts_10m": 8 + 3 * rng.randn(n_hours),
        "city_amman": 1.0,
        "city_irbid": 0.0,
        "city_aqaba": 0.0,
    })


@pytest.fixture
def prepared_data():
    df = _make_synthetic_data()
    variables = [
        "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
        "pressure_msl", "dew_point_2m", "shortwave_radiation", "wind_gusts_10m",
    ]
    targets = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"]

    df = engineer_features(df, variables=variables, lags=[1, 6, 24, 168], rolling_windows=[24, 168])
    train, val, test = split_data(df, train_years=0.6, val_years=0.2, test_years=0.2)

    feature_cols = [c for c in train.columns if c != "date"]
    numeric_cols = [c for c in feature_cols if train[c].dtype in [np.float64, np.float32]]
    train, val, test, scaler = normalize_data(train, val, numeric_cols, test=test)

    window_size = 48  # Smaller for testing speed
    horizons = [6, 24]

    train_ds = WeatherDataset(train, feature_cols, targets, window_size, horizons)
    val_ds = WeatherDataset(val, feature_cols, targets, window_size, horizons)
    test_ds = WeatherDataset(test, feature_cols, targets, window_size, horizons)

    return {
        "train_loader": DataLoader(train_ds, batch_size=32, shuffle=True),
        "val_loader": DataLoader(val_ds, batch_size=32),
        "test_loader": DataLoader(test_ds, batch_size=32),
        "feature_cols": feature_cols,
        "targets": targets,
        "horizons": horizons,
        "scaler": scaler,
    }


def test_gru_training_converges(prepared_data, tmp_path):
    """GRU model should train and produce finite predictions on synthetic data."""
    d = prepared_data
    model = GRUForecaster(
        input_size=len(d["feature_cols"]),
        hidden_size=32,
        num_layers=1,
        num_horizons=len(d["horizons"]),
        num_targets=len(d["targets"]),
        dropout=0.0,
    )
    trainer = Trainer(
        model=model, train_loader=d["train_loader"], val_loader=d["val_loader"],
        learning_rate=0.001, weight_decay=0.0001,
        scheduler_patience=3, early_stopping_patience=5,
        max_epochs=10, log_dir=str(tmp_path / "gru"), device="cpu",
    )
    trainer.train()
    trainer.load_best()

    model.train(False)
    with torch.no_grad():
        for x, y in d["test_loader"]:
            pred = model(x)
            assert not torch.isnan(pred).any()
            assert not torch.isinf(pred).any()
            break


def test_tft_training_converges(prepared_data, tmp_path):
    """TFT model should train and produce finite predictions on synthetic data."""
    d = prepared_data
    model = TemporalFusionTransformer(
        input_size=len(d["feature_cols"]),
        hidden_size=16,
        num_heads=4,
        num_horizons=len(d["horizons"]),
        num_targets=len(d["targets"]),
        quantiles=[0.1, 0.5, 0.9],
        dropout=0.0,
    )
    loss_fn = QuantileLoss(quantiles=[0.1, 0.5, 0.9])
    trainer = Trainer(
        model=model, train_loader=d["train_loader"], val_loader=d["val_loader"],
        learning_rate=0.001, weight_decay=0.0001,
        scheduler_patience=3, early_stopping_patience=5,
        max_epochs=10, log_dir=str(tmp_path / "tft"), device="cpu",
        loss_fn=loss_fn,
    )
    trainer.train()
    trainer.load_best()

    model.train(False)
    with torch.no_grad():
        for x, y in d["test_loader"]:
            pred = model(x)
            assert pred.shape[-1] == 3  # 3 quantiles
            assert not torch.isnan(pred).any()
            break

    importance = model.get_variable_importance()
    assert importance.shape == (len(d["feature_cols"]),)
    assert torch.allclose(importance.sum(), torch.tensor(1.0), atol=1e-4)
```

- [ ] **Step 2: Run the integration test**

```bash
cd jordan-weather-forecast && python -m pytest tests/test_integration.py -v --timeout=120
```

Expected: All tests PASS (may take ~30-60 seconds)

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: end-to-end integration test with synthetic data"
```

---

### Task 11: README

**Files:**
- Create: `jordan-weather-forecast/README.md`

- [ ] **Step 1: Write the README**

```markdown
# Jordan Weather Forecasting Pipeline

Research pipeline comparing GRU and Temporal Fusion Transformer (TFT) models for multi-horizon weather forecasting across three Jordanian cities (Amman, Irbid, Aqaba).

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Full pipeline: fetch data, train both models, assess
python main.py

# Fetch data only
python main.py --fetch-only

# Train a specific model
python main.py --model gru
python main.py --model tft

# Re-assess saved models
python main.py --assess-only
```

## Configuration

All hyperparameters are in `config/default.yaml`.

## Results

After training, find outputs in `experiments/logs/`:
- `comparison.csv` -- GRU vs TFT metrics across all horizons/cities/variables
- `{model}_latest/metrics.csv` -- per-epoch training metrics
- `{model}_latest/plots/` -- prediction plots
- `plots/` -- degradation curves

## Tests

```bash
python -m pytest tests/ -v
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and usage instructions"
```
