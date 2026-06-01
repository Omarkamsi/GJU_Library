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
