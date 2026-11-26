"""Tests for the forecasting module (src/forecast.py) and the /ml/forecast-stock endpoint.
These tests run against the real data in sample_data/stok_harian.csv.
"""

import pathlib
import json
import pandas as pd
import pytest
from fastapi.testclient import TestClient
import yaml

from src import forecast as f_mod
from src.api import app

client = TestClient(app)

# Helper to load config

def load_config():
    cfg_path = pathlib.Path(__file__).parents[1] / "configs" / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


cfg = load_config()

def test_target_creation_horizon_1():
    df = f_mod._load_data()
    X, y, _ = f_mod._preprocess(df.copy(), cfg, horizon=1)
    # Choose a SKU with at least two dates
    sku = df['id_barang'].value_counts().idxmax()
    sub = df[df['id_barang'] == sku].sort_values('tanggal')
    if len(sub) < 2:
        pytest.skip('SKU does not have enough rows')
    origin_date = sub.iloc[0]['tanggal']
    target_date = origin_date + pd.Timedelta(days=1)
    future_row = df[(df['id_barang'] == sku) & (df['tanggal'] == target_date)]
    if future_row.empty:
        # future date missing means target was dropped
        assert target_date not in X.index
    else:
        # locate the row in X corresponding to the origin date
        idx = X[(X[cfg['data']['kolom']['id_barang']] == sku) & (X[cfg['data']['kolom']['tanggal']] == origin_date)].index[0]
        target_val = y.loc[idx]
        assert target_val == future_row.iloc[0]['stok_akhir']

def test_target_creation_horizon_3():
    df = f_mod._load_data()
    X, y, _ = f_mod._preprocess(df.copy(), cfg, horizon=3)
    for idx, row in X.iterrows():
        sku = row[cfg['data']['kolom']['id_barang']]
        date = row[cfg['data']['kolom']['tanggal']]
        exists = not df[(df['id_barang'] == sku) & (df['tanggal'] == date + pd.Timedelta(days=3))].empty
        assert exists

def test_no_leakage_features():
    # Load raw data and run full preprocessing (clean + engineer)
    df_raw = f_mod._load_data()
    # _preprocess returns X, y, feature_names. X already includes engineered features.
    X, _, feature_names = f_mod._preprocess(df_raw.copy(), cfg, horizon=1)
    # Verify that all configured numeric features are present after engineering.
    numeric = cfg['features']['numerik']
    for col in numeric:
        assert col in X.columns, f"Numeric feature {col} missing after engineering"
    # Ensure metadata columns are not part of the model feature list.
    for meta in ['tanggal', 'target_date', 'future_stock']:
        assert meta not in feature_names, f"Metadata column {meta} should not be a model feature"



def test_train_and_load_model(tmp_path, monkeypatch):
    model = f_mod.train_forecast_model(horizon=7)
    assert model is not None
    model_path = tmp_path / "tmp_forecast.joblib"
    import joblib
    joblib.dump(model, model_path)
    monkeypatch.setattr(f_mod, "_FORECAST_MODEL_PATH", model_path)
    loaded = f_mod.load_forecast_model()
    assert isinstance(loaded, type(model))

def test_predict_future_stock_logic(monkeypatch):
    item = {
        "id_barang": "PR001",
        "nama_barang": "Lotus Biscoff",
        "batas_minimum": 5.0,
        "stok_saat_ini": 10.0,
        "barang_masuk": 2.0,
        "barang_keluar": 1.0,
        "avg_keluar_7h": 1.0,
        "total_masuk_7h": 14.0,
        "total_keluar_7h": 7.0,
        "kategori": "Roti Manis",
        "rasa": "Lotus Biscoff",
    }
    # Patch model.predict to return fixed values
    class DummyModel:
        def __init__(self, val):
            self.val = val
        def predict(self, X):
            return [self.val]
    for stock, expected in [(-2, "habis"), (0, "habis"), (4, "menipis"), (6, "aman")]:
        dummy = DummyModel(stock)
        pred = f_mod.predict_future_stock(item, horizon=1, model=dummy, cfg=cfg)
        assert pred["predicted_status"] == expected

def test_endpoint_forecast_success():
    payload = {
        "items": [
            {
                "id_barang": "PR001",
                "nama_barang": "Lotus Biscoff",
                "batas_minimum": 5.0,
                "stok_saat_ini": 10.0,
                "barang_masuk": 2.0,
                "barang_keluar": 1.0,
                "avg_keluar_7h": 1.0,
                "total_masuk_7h": 14.0,
                "total_keluar_7h": 7.0,
                "kategori": "Roti Manis",
                "rasa": "Lotus Biscoff",
            }
        ],
        "horizon_days": 7,
    }
    resp = client.post("/ml/forecast-stock", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_items"] == 1
    result = data["results"][0]
    assert result["id_barang"] == "PR001"
    assert "predicted_stock" in result
    assert result["predicted_status"] in ["aman", "menipis", "habis"]

def test_endpoint_invalid_horizon():
    payload = {"items": [], "horizon_days": 3}
    resp = client.post("/ml/forecast-stock", json=payload)
    assert resp.status_code in (400, 422)
