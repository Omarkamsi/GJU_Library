# Jordan Weather Forecasting Pipeline — Design Spec

## Overview

A research-oriented weather forecasting pipeline for Jordan, comparing GRU (baseline) and Temporal Fusion Transformer (TFT) architectures across multiple forecast horizons. Uses Open-Meteo Historical API for data, targets temperature, humidity, and wind speed predictions for three Jordanian cities.

## Goals

- Explore how GRU and TFT compare for multi-horizon weather forecasting in Jordan's climate
- Produce interpretable results (TFT variable importance, degradation curves)
- Achieve MAE <1.2°C for 24h temperature forecasts, R² >0.90
- Maintain full reproducibility via config-driven experiments and cached data

## Data

### Source

Open-Meteo Historical API (free, no registration, uses ERA5 under the hood).

### Cities

| City   | Latitude | Longitude |
|--------|----------|-----------|
| Amman  | 31.95°N  | 35.93°E   |
| Irbid  | 32.56°N  | 35.85°E   |
| Aqaba  | 29.53°N  | 35.01°E   |

### Variables Fetched

- temperature_2m
- relative_humidity_2m
- wind_speed_10m
- pressure_msl
- dew_point_2m
- shortwave_radiation
- wind_gusts_10m

### Feature Engineering

- **Lag features:** t-1, t-6, t-24, t-168
- **Rolling stats:** 24h and 168h moving averages
- **Cyclical encodings:** sin/cos for hour-of-day and day-of-year
- **Derived:** dew point depression (temperature - dew point)

### Data Split

Walk-forward temporal split (no shuffling):
- Train: years 1–7
- Validation: years 8–9
- Test: year 10

## Project Structure

```
jordan-weather-forecast/
├── config/
│   └── default.yaml          # All hyperparams, city coords, feature lists
├── data/
│   ├── fetch.py              # Open-Meteo API client
│   ├── preprocess.py         # Feature engineering, normalization, splits
│   └── dataset.py            # PyTorch Dataset for sliding windows
├── models/
│   ├── gru.py                # GRU baseline
│   └── tft.py                # Temporal Fusion Transformer
├── training/
│   ├── trainer.py            # Training loop, early stopping, checkpointing
│   └── evaluate.py           # Metrics computation, comparison tables
├── experiments/
│   └── logs/                 # CSV logs, metric summaries, loss curves
├── notebooks/
│   └── analysis.ipynb        # Visualization and result exploration
├── main.py                   # Entry point: fetch → preprocess → train → evaluate
├── requirements.txt
└── README.md
```

## Models

### GRU Baseline

- 2-layer GRU, hidden size 128
- Input: 168-hour sliding window of all features
- Output: multi-horizon predictions (6h, 12h, 24h, 48h, 72h) for 3 targets (temp, humidity, wind speed)
- Dropout: 0.3 between layers
- Linear head: final hidden state → output dimensions
- Loss: MSE

### Temporal Fusion Transformer

- Based on the Google Research TFT paper
- Components:
  - Variable Selection Networks (learned feature importance)
  - Gated Residual Networks (GRN)
  - Multi-head attention (4 heads)
  - Quantile output (10th, 50th, 90th percentiles)
- Hidden size: 64 (constrained for 4GB VRAM on RTX 3050 Ti)
- Input window: 168 hours
- Batch size: 32
- Loss: Quantile Loss for training; MSE computed on the 50th percentile (median) output for direct comparison with GRU

### Shared Training Config

- Optimizer: AdamW, weight decay 1e-4
- Scheduler: ReduceLROnPlateau, patience=5
- Early stopping: patience=10 on validation loss
- Unified model: city as one-hot categorical feature

## Evaluation

### Metrics (per city, per horizon, per variable)

- MAE (primary) — target <1.2°C for 24h temperature
- RMSE
- R² — target >0.90
- MAPE

### Outputs

- GRU vs TFT summary table across all horizons/cities/variables
- MAE vs forecast horizon degradation curves (6h→72h)
- Training vs validation loss curves
- TFT variable importance scores
- Per-city performance breakdown

### Experiment Tracking

Each run saves to `experiments/logs/{model}_{timestamp}/`:
- `config.yaml` — frozen hyperparams
- `metrics.csv` — epoch-by-epoch train/val metrics
- `test_results.csv` — final test performance
- `model_best.pt` — best checkpoint by val loss

Aggregated comparison: `experiments/logs/comparison.csv`

### Visualizations (auto-generated via matplotlib)

- Actual vs predicted time series (sample weeks)
- Error distribution histograms
- Horizon degradation curves
- Feature importance bar charts (TFT)

## Training & Inference Flow

1. Load config from `config/default.yaml`
2. Fetch data (or load cached CSV from `data/raw/`)
3. Preprocess: feature engineering → StandardScaler (fit on train only) → save scaler
4. Create PyTorch Datasets with sliding windows
5. Train GRU → evaluate → save results
6. Train TFT → evaluate → save results
7. Generate comparison table and plots

### Caching

- Raw API responses: CSV in `data/raw/`
- Preprocessed tensors: `data/processed/`

### CLI Interface

```bash
python main.py                          # full pipeline
python main.py --fetch-only             # just download data
python main.py --model gru              # train only GRU
python main.py --model tft              # train only TFT
python main.py --evaluate-only          # re-run eval on saved checkpoints
```

## Dependencies

- PyTorch (with CUDA)
- openmeteo-requests, requests-cache
- pandas, numpy, scikit-learn
- matplotlib
- pyyaml

## Compute Environment

- RTX 3050 Ti (4GB VRAM)
- 32GB RAM
- Batch sizes and hidden dims chosen to fit within VRAM constraints
