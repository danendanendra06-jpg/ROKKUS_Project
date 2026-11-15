"""
train.py – Latih dan Simpan Model Terbaik
==========================================
Capstone Asah 2026 | Tim A26-CS159

Melatih minimal 3 model:
  1. Logistic Regression
  2. Random Forest
  3. Gradient Boosting
  (+ tuning opsional via GridSearchCV jika --tune diberikan)

Model terbaik (berdasarkan F1 Macro pada test set) disimpan ke:
  models/best_model.joblib
  models/metadata.json

Jalankan:
  python src/train.py
  python src/train.py --tune   # aktifkan GridSearchCV (lebih lambat)
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline

from preprocessing import run_preprocessing
from evaluate import evaluate_model, save_comparison_report

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_config_path() -> Path:
    return Path(__file__).parent.parent / "configs" / "config.yaml"


def _load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_output(base: Path, path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (base / p).resolve()


def _import_class(dotted_path: str):
    """Import class dari string seperti 'sklearn.ensemble.RandomForestClassifier'."""
    parts = dotted_path.rsplit(".", 1)
    module = importlib.import_module(parts[0])
    return getattr(module, parts[1])


# ---------------------------------------------------------------------------
# Fungsi utama training
# ---------------------------------------------------------------------------

def train_all_models(
    config_path: Path | None = None,
    use_tuning: bool = False,
) -> dict:
    """
    Latih semua model yang terdaftar di config, bandingkan, simpan yang terbaik.

    Returns
    -------
    dict berisi hasil evaluasi semua model dan model terbaik.
    """
    if config_path is None:
        config_path = _get_config_path()

    cfg = _load_config(config_path)
    base_dir = config_path.parent.parent

    # ── Preprocessing ────────────────────────────────────────────────────
    logger.info("⏳ Menjalankan preprocessing …")
    prep = run_preprocessing(config_path)
    X_train = prep["X_train"]
    X_test  = prep["X_test"]
    y_train = prep["y_train"]
    y_test  = prep["y_test"]
    base_pipeline = prep["pipeline"]    # ColumnTransformer pipeline

    kelas = cfg["label_rules"]["kelas"]
    model_cfgs = cfg["models"]["daftar"]
    tuning_cfg = cfg["models"]["tuning"]

    # ── Latih tiap model ─────────────────────────────────────────────────
    all_results: list[dict] = []
    trained_models: dict[str, Pipeline] = {}

    for mcfg in model_cfgs:
        nama  = mcfg["nama"]
        kelas_model = _import_class(mcfg["kelas"])
        params = mcfg.get("params", {})

        logger.info(f"\n── Melatih {nama} ──")

        # Buat full pipeline: preprocessor + classifier
        full_pipeline = Pipeline([
            ("preprocessor", base_pipeline.named_steps["preprocessor"]),
            ("classifier",   kelas_model(**params)),
        ])

        if use_tuning and tuning_cfg.get("aktif", False) and nama in tuning_cfg.get("param_grid", {}):
            logger.info(f"   GridSearchCV aktif untuk {nama} …")
            pg = {f"classifier__{k}": v for k, v in tuning_cfg["param_grid"][nama].items()}
            gs = GridSearchCV(
                full_pipeline,
                param_grid=pg,
                cv=tuning_cfg["cv_folds"],
                scoring=tuning_cfg["scoring"],
                n_jobs=-1,
                verbose=1,
            )
            gs.fit(X_train, y_train)
            final_model = gs.best_estimator_
            logger.info(f"   Best params: {gs.best_params_}")
        else:
            full_pipeline.fit(X_train, y_train)
            final_model = full_pipeline

        trained_models[nama] = final_model

        # Evaluasi
        metrics = evaluate_model(
            model=final_model,
            X_test=X_test,
            y_test=y_test,
            model_name=nama,
            kelas=kelas,
            config_path=config_path,
        )
        all_results.append(metrics)

        logger.info(
            f"   Accuracy={metrics['accuracy']:.4f} | "
            f"F1_macro={metrics['f1_macro']:.4f}"
        )

    # ── Pilih model terbaik ───────────────────────────────────────────────
    # Kriteria: F1 Macro tertinggi (lebih adil untuk data imbalanced)
    best = max(all_results, key=lambda x: x["f1_macro"])
    best_name  = best["model_name"]
    best_model = trained_models[best_name]

    logger.info(f"\n🏆 Model terbaik: {best_name} (F1_macro={best['f1_macro']:.4f})")

    # ── Simpan model ──────────────────────────────────────────────────────
    model_dir = _resolve_output(base_dir, cfg["output"]["model_dir"])
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / cfg["output"]["model_file"]
    joblib.dump(best_model, model_path)
    logger.info(f"💾 Model disimpan → {model_path}")

    # Metadata
    feat_cfg = cfg["features"]
    all_features = feat_cfg["numerik"] + feat_cfg["kategorik"]

    metadata = {
        "versi":       "1.0.0",
        "model_nama":  best_name,
        "fitur":       all_features,
        "label_kelas": kelas,
        "tanggal_latih": datetime.now().isoformat(),
        "metrik_test": {
            "accuracy":        round(best["accuracy"], 4),
            "f1_macro":        round(best["f1_macro"], 4),
            "f1_per_kelas":    {k: round(v, 4) for k, v in best["f1_per_kelas"].items()},
        },
        "config_path": str(config_path),
        "data_path":   cfg["data"]["path_data"],
    }
    meta_path = _resolve_output(base_dir, cfg["output"]["metadata_file"])
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    logger.info(f"📄 Metadata disimpan → {meta_path}")

    # ── Laporan perbandingan ──────────────────────────────────────────────
    save_comparison_report(all_results, config_path)

    return {
        "all_results":  all_results,
        "best_name":    best_name,
        "best_model":   best_model,
        "model_path":   model_path,
        "metadata":     metadata,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Train ROKKUS ML models")
    parser.add_argument(
        "--tune", action="store_true",
        help="Aktifkan GridSearchCV tuning (lebih lambat)"
    )
    parser.add_argument(
        "--config", type=Path, default=None,
        help="Path ke config.yaml (default: configs/config.yaml)"
    )
    args = parser.parse_args()

    cfg_path = args.config or _get_config_path()
    result = train_all_models(config_path=cfg_path, use_tuning=args.tune)

    print("\n" + "=" * 60)
    print("HASIL TRAINING")
    print("=" * 60)
    for r in result["all_results"]:
        print(
            f"  {r['model_name']:<22} "
            f"Acc={r['accuracy']:.4f}  F1_macro={r['f1_macro']:.4f}"
        )
    print(f"\n🏆 Model Terbaik : {result['best_name']}")
    print(f"   Disimpan di   : {result['model_path']}")
