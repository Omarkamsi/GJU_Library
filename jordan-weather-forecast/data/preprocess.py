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
