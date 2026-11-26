"""forecast.py – Simple time‑series forecasting for stock levels

This module implements a lightweight forecasting pipeline that re‑uses many of the
pre‑processing utilities from ``preprocessing.py`` but creates a *regression*
target: the ``stok_akhir`` value *horizon_days* days in the future.

The design follows the same principles as the classification pipeline:

-   Pure‑Python, no external services.
-   Features are built **only** from data that would be available at prediction
    time (no look‑ahead leakage).
-   A chronological train/test split is used when training the model.
-   The model is stored under ``models/forecast_model.joblib`` and lazily loaded
    by the API endpoint.

If the model file does not exist the first request to ``/ml/forecast-stock``
triggers an on‑demand training run.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Tuple, List, Dict, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

# Project‑wide constants (mirroring src.api)
_ML_DIR = Path(__file__).parent.parent
_DATA_PATH = _ML_DIR / "sample_data" / "stok_harian.csv"
_CONFIG_PATH = _ML_DIR / "configs" / "config.yaml"
_FORECAST_MODEL_PATH = _ML_DIR / "models" / "forecast_model.joblib"

logger = logging.getLogger(__name__)


def _load_data() -> pd.DataFrame:
    """Load the historical CSV and parse dates.

    Returns
    -------
    pd.DataFrame
        Raw data frame with original columns.
    """
    df = pd.read_csv(_DATA_PATH, parse_dates=["tanggal"], encoding="utf-8")
    return df


def _preprocess(df: pd.DataFrame, cfg: dict, horizon: int) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """Create features and regression target for a given horizon.

    Parameters
    ----------
    df : pd.DataFrame
        Raw data.
    cfg : dict
        Configuration dictionary loaded from ``config.yaml``.
    horizon : int
        Number of days ahead to forecast (must be > 0).

    Returns
    -------
    X : pd.DataFrame
        Feature matrix.
    y : pd.Series
        Target vector (future ``stok_akhir``).
    feature_names : list[str]
        List of column names that will be fed to the model.
    """
    from src import preprocessing as pp  # local import to avoid circular deps

    # 1️⃣ Basic cleaning / rolling features (same as classification)
    df = pp.clean_data(df, cfg)  # drop duplicates, sort, etc.
    df = pp.engineer_features(df, cfg)

    # 2️⃣ Build regression target: future stock after ``horizon`` days per SKU
    # Instead of a simple shift (which assumes daily data), we compute the target
    # by looking up the row with date = current_date + horizon days for the same SKU.
    # This works even when observations are irregular; if the future date does not
    # exist in the data we drop that row (insufficient history for that horizon).
    # Sorting is omitted to preserve original data order as expected by tests
    # df = df.sort_values([cfg["data"]["kolom"]["id_barang"], cfg["data"]["kolom"]["tanggal"]])
    id_col = cfg["data"]["kolom"]["id_barang"]
    date_col = cfg["data"]["kolom"]["tanggal"]
    stock_col = cfg["data"]["kolom"]["stok_akhir"]
    # compute the calendar date we need to look up
    df["target_date"] = df[date_col] + pd.Timedelta(days=horizon)
    # prepare a lookup frame with future stock per SKU/date
    df_future = df[[id_col, date_col, stock_col]].copy()
    df_future = df_future.rename(columns={date_col: "target_date", stock_col: "future_stock"})
    # merge to get future_stock; rows without a matching future date will have NaN
    df = df.merge(
        df_future[[id_col, "target_date", "future_stock"]],
        on=[id_col, "target_date"],
        how="left",
        suffixes=("", "_y"),
    )
    # drop rows where we cannot compute the target (future_stock is NaN)
    df = df.dropna(subset=["future_stock"])

    # 3️⃣ Select the same numeric / categorical feature lists used for classification
    feat_cfg = cfg["features"]
    numeric_feats = feat_cfg["numerik"]
    categorical_feats = feat_cfg["kategorik"]
    X = df[[id_col, date_col] + numeric_feats + categorical_feats]
    # Preserve target_date as metadata for split (not a model feature)
    X['target_date'] = df['target_date']
    # No index is set; keep 'tanggal' column for tests and ensure unique integer index.

    y = df["future_stock"].astype(float)

    return X, y, numeric_feats + categorical_feats


def train_forecast_model(horizon: int = 7) -> Pipeline:
    """Train a GradientBoostingRegressor on the historic data.

    The function reads ``config.yaml`` to obtain feature lists, builds the
    training set with the requested horizon, performs a chronological train/test
    split (using the same ``time_split`` helper from ``preprocessing.py``) and
    finally fits a ``Pipeline`` consisting of a ``ColumnTransformer`` and a
    ``GradientBoostingRegressor``.

    The trained model is saved to ``models/forecast_model.joblib`` and also
    returned.
    """
    import yaml
    from src import preprocessing as pp

    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    df_raw = _load_data()
    X, y, feature_names = _preprocess(df_raw, cfg, horizon)

    # Chronological split with purge gap (forecast‑specific)
    
    df_all = pd.concat([X, y], axis=1)
    date_col = cfg["data"]["kolom"]["tanggal"]
    # Determine cutoff date using unique origin dates and split proportion
    unique_dates = sorted(df_all[date_col].dropna().unique())
    cutoff_idx = int(len(unique_dates) * (1 - cfg["split"]["test_size"]))
    cutoff_date = pd.Timestamp(unique_dates[cutoff_idx])
    # Training rows: origin date < cutoff AND target_date <= cutoff
    train_mask = (df_all[date_col] < cutoff_date) & (df_all["target_date"] <= cutoff_date)
    # Testing rows: origin date >= cutoff
    test_mask = df_all[date_col] >= cutoff_date
    # Apply masks (purge rows are dropped automatically)
    X_train = X[train_mask]
    y_train = y[train_mask]
    X_test = X[test_mask]
    y_test = y[test_mask]
    logger.info(
        "Forecast split (horizon=%s): train=%d, purge=%d, test=%d",
        horizon,
        len(X_train),
        len(df_all) - len(X_train) - len(X_test),
        len(X_test),
    )
    


    # Build preprocessing pipeline
    numeric_feats = [c for c in feature_names if c in cfg["features"]["numerik"]]
    categorical_feats = [c for c in feature_names if c in cfg["features"]["kategorik"]]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_feats),
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical_feats),
        ],
        remainder="drop",
    )

    model = GradientBoostingRegressor(random_state=42)
    pipeline = Pipeline([("preprocessor", preprocessor), ("regressor", model)])

    pipeline.fit(X_train, y_train)
    # Save model for later reuse
    joblib.dump(pipeline, _FORECAST_MODEL_PATH)
    logger.info("Forecast model trained and saved to %s", _FORECAST_MODEL_PATH)
    return pipeline


def load_forecast_model() -> Pipeline:
    """Load the persisted model or train a new one on‑demand."""
    if _FORECAST_MODEL_PATH.exists():
        model = joblib.load(_FORECAST_MODEL_PATH)
        logger.info("Loaded existing forecast model from %s", _FORECAST_MODEL_PATH)
        return model
    else:
        logger.warning("Forecast model not found – training a new one with default horizon=7")
        return train_forecast_model(horizon=7)


def predict_future_stock(item: Dict[str, Any], horizon: int, model: Pipeline, cfg: dict) -> Dict[str, Any]:
    """Predict future stock for a single SKU.

    Parameters
    ----------
    item : dict
        Must contain the raw columns required by the feature list (e.g.
        ``stok_saat_ini``, ``batas_minimum`` and the categorical fields).
    horizon : int
        Forecast horizon in days.
    model : Pipeline
        Trained forecasting pipeline.
    cfg : dict
        Configuration dictionary.

    Returns
    -------
    dict
        ``{"predicted_stock": float, "predicted_status": str}``
    """
    # Build a one‑row DataFrame with the same columns as training
    df_row = pd.DataFrame([item])
    # Ensure required derived features exist
    # days_of_cover and rasio_stok are derived in preprocessing; compute simple defaults if missing
    if "days_of_cover" not in df_row.columns:
        df_row["days_of_cover"] = 1.0
    if "rasio_stok" not in df_row.columns:
        stok = item.get("stok_saat_ini", item.get("stok_akhir", 0.0))
        batas = item.get("batas_minimum", 1.0)
        df_row["rasio_stok"] = float(stok) / max(float(batas), 1.0)
    # Ensure column order matches training features
    feature_order = cfg["features"]["numerik"] + cfg["features"]["kategorik"]
    X_row = df_row[feature_order]
    pred_stock = float(model.predict(X_row)[0])
    # Determine future status using the same rule‑based logic as classification
    batas = item["batas_minimum"]
    # Simple rule: if pred <= 0 -> habis; elif pred <= batas -> menipis; else aman
    if pred_stock <= 0:
        status = "habis"
    elif pred_stock <= batas:
        status = "menipis"
    else:
        status = "aman"
    return {"predicted_stock": pred_stock, "predicted_status": status}