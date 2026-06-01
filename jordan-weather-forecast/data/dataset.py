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
