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
