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
