"""
evaluate.py – Evaluasi dan Laporan Perbandingan Model
======================================================
Capstone Asah 2026 | Tim A26-CS159

Metrik yang dihitung (sama untuk semua model):
  - Accuracy
  - Precision, Recall, F1 (macro average)
  - F1 per kelas (aman / menipis / habis)
  - Confusion Matrix (disimpan sebagai gambar)

Output:
  reports/model_comparison.csv
  reports/model_comparison.md
  reports/figures/cm_<ModelName>.png
  reports/figures/metric_comparison.png
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # non-interactive backend untuk server/CI
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yaml
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_output(base: Path, path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (base / p).resolve()


# ---------------------------------------------------------------------------
# Evaluasi satu model
# ---------------------------------------------------------------------------

def evaluate_model(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
    kelas: list[str],
    config_path: Path,
    save_figures: bool = True,
) -> dict:
    """
    Evaluasi model pada data test dan (opsional) simpan confusion matrix.

    Returns
    -------
    dict berisi semua metrik evaluasi.
    """
    cfg      = _load_config(config_path)
    base_dir = config_path.parent.parent
    fig_dir  = _resolve_output(base_dir, cfg["output"]["figures_dir"])
    fig_dir.mkdir(parents=True, exist_ok=True)

    y_pred = model.predict(X_test)

    acc  = accuracy_score(y_test, y_pred)
    f1_m = f1_score(y_test, y_pred, average="macro", zero_division=0)
    prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec  = recall_score(y_test, y_pred, average="macro", zero_division=0)

    # F1 per kelas
    f1_per = {}
    for k in kelas:
        mask = y_test == k
        if mask.sum() > 0:
            f1_per[k] = round(f1_score(y_test, y_pred, labels=[k], average="micro", zero_division=0), 4)
        else:
            f1_per[k] = None

    logger.info(f"\n[{model_name}] Classification Report:\n"
                + classification_report(y_test, y_pred, zero_division=0))

    if save_figures:
        _plot_confusion_matrix(y_test, y_pred, kelas, model_name, fig_dir)

    return {
        "model_name":   model_name,
        "accuracy":     acc,
        "precision":    prec,
        "recall":       rec,
        "f1_macro":     f1_m,
        "f1_per_kelas": f1_per,
    }


# ---------------------------------------------------------------------------
# Plot confusion matrix
# ---------------------------------------------------------------------------

def _plot_confusion_matrix(
    y_true: pd.Series,
    y_pred: np.ndarray,
    kelas: list[str],
    model_name: str,
    fig_dir: Path,
) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=kelas)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=kelas, yticklabels=kelas,
        linewidths=0.5, ax=ax,
    )
    ax.set_xlabel("Predicted", fontsize=11)
    ax.set_ylabel("Actual", fontsize=11)
    ax.set_title(f"Confusion Matrix – {model_name}", fontsize=12, fontweight="bold")

    out_path = fig_dir / f"cm_{model_name.replace(' ', '_')}.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    logger.info(f"   Confusion matrix disimpan → {out_path}")


# ---------------------------------------------------------------------------
# Laporan perbandingan semua model
# ---------------------------------------------------------------------------

def save_comparison_report(all_results: list[dict], config_path: Path) -> None:
    """
    Simpan:
      - reports/model_comparison.csv
      - reports/model_comparison.md   (tabel + alasan pemilihan + keterbatasan)
      - reports/figures/metric_comparison.png
    """
    cfg      = _load_config(config_path)
    base_dir = config_path.parent.parent
    report_dir = _resolve_output(base_dir, cfg["output"]["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    fig_dir  = _resolve_output(base_dir, cfg["output"]["figures_dir"])
    fig_dir.mkdir(parents=True, exist_ok=True)

    kelas = cfg["label_rules"]["kelas"]

    # ── CSV ───────────────────────────────────────────────────────────────
    rows = []
    for r in all_results:
        row = {
            "Model":       r["model_name"],
            "Accuracy":    round(r["accuracy"], 4),
            "Precision_macro": round(r["precision"], 4),
            "Recall_macro":    round(r["recall"], 4),
            "F1_macro":    round(r["f1_macro"], 4),
        }
        for k in kelas:
            val = r["f1_per_kelas"].get(k)
            row[f"F1_{k}"] = round(val, 4) if val is not None else "N/A"
        rows.append(row)

    df_cmp = pd.DataFrame(rows)
    csv_path = report_dir / "model_comparison.csv"
    df_cmp.to_csv(csv_path, index=False)
    logger.info(f"📊 Comparison CSV disimpan → {csv_path}")

    # ── Bar chart perbandingan metrik ─────────────────────────────────────
    _plot_metric_comparison(df_cmp, kelas, fig_dir)

    # ── Markdown report ───────────────────────────────────────────────────
    best_row = df_cmp.loc[df_cmp["F1_macro"].idxmax()]
    _save_markdown_report(df_cmp, best_row, kelas, report_dir, cfg)


def _plot_metric_comparison(
    df_cmp: pd.DataFrame,
    kelas: list[str],
    fig_dir: Path,
) -> None:
    models = df_cmp["Model"].tolist()
    metric_cols = ["Accuracy", "F1_macro"] + [f"F1_{k}" for k in kelas]
    metric_cols = [c for c in metric_cols if c in df_cmp.columns]

    x = np.arange(len(models))
    width = 0.15
    n_metrics = len(metric_cols)

    fig, ax = plt.subplots(figsize=(11, 5))
    for i, col in enumerate(metric_cols):
        vals = pd.to_numeric(df_cmp[col], errors="coerce").fillna(0).tolist()
        offset = (i - n_metrics / 2) * width + width / 2
        bars = ax.bar(x + offset, vals, width, label=col)

    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("Perbandingan Metrik antar Model – ROKKUS ML", fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="y", alpha=0.3)

    out_path = fig_dir / "metric_comparison.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    logger.info(f"📊 Bar chart disimpan → {out_path}")


def _save_markdown_report(
    df_cmp: pd.DataFrame,
    best_row: pd.Series,
    kelas: list[str],
    report_dir: Path,
    cfg: dict,
) -> None:
    lines = []
    lines.append("# Laporan Perbandingan Model – ROKKUS ML")
    lines.append("")
    lines.append(f"> **Tanggal evaluasi**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> **Data**: {cfg['data']['path_data']}")
    lines.append(f"> **Split**: train (awal {int((1-cfg['split']['test_size'])*100)}%) / test (akhir {int(cfg['split']['test_size']*100)}%) berbasis waktu")
    lines.append("")

    # Tabel perbandingan
    lines.append("## Tabel Perbandingan")
    lines.append("")
    lines.append(df_cmp.to_markdown(index=False))
    lines.append("")

    # Figures
    lines.append("## Confusion Matrix")
    lines.append("")
    for _, row in df_cmp.iterrows():
        nm = row["Model"].replace(" ", "_")
        lines.append(f"### {row['Model']}")
        lines.append(f"![Confusion Matrix {row['Model']}](figures/cm_{nm}.png)")
        lines.append("")

    lines.append("## Perbandingan Metrik (Bar Chart)")
    lines.append("")
    lines.append("![Metric Comparison](figures/metric_comparison.png)")
    lines.append("")

    # Alasan pemilihan
    lines.append("## Alasan Pemilihan Model Terbaik")
    lines.append("")
    lines.append(
        f"Model terpilih adalah **{best_row['Model']}** dengan F1 Macro = "
        f"**{best_row['F1_macro']:.4f}** dan Accuracy = **{best_row['Accuracy']:.4f}** "
        "pada test set."
    )
    lines.append("")
    lines.append(
        "F1 Macro dipilih sebagai kriteria utama karena distribusi kelas "
        "(_aman_, _menipis_, _habis_) tidak seimbang, dan kelas minoritas "
        "(_habis_, _menipis_) lebih krusial secara bisnis. "
        "F1 Macro memberikan bobot setara pada tiap kelas terlepas dari frekuensinya."
    )
    lines.append("")

    # Keterbatasan
    lines.append("## Keterbatasan dan Catatan")
    lines.append("")
    lines.append("### Label dari Aturan Eksplisit (Rule-Based Labeling)")
    lines.append(
        "Label `status_stok` dibuat dari aturan deterministic berbasis `stok_akhir` "
        "dan `batas_minimum` yang didefinisikan di `configs/config.yaml`. "
        "Ini berarti model _mempelajari ulang_ aturan tersebut dari fitur-fitur turunannya "
        "(misalnya `days_of_cover`, `rasio_stok`). "
        "Dalam konteks produksi, label asli dari tim operasional ROKKUS akan "
        "membuat evaluasi lebih jujur."
    )
    lines.append("")
    lines.append("### Potensi Kebocoran Data (Data Leakage)")
    lines.append(
        "Fitur `stok_saat_ini` (alias `stok_akhir`) dan `batas_minimum` berkaitan "
        "langsung dengan label. Meskipun tidak dimasukkan _verbatim_ sebagai fitur label, "
        "turunannya (`days_of_cover`, `rasio_stok`) sangat kuat secara prediktif. "
        "Hal ini wajar karena memang fitur-fitur itu yang relevan secara bisnis, "
        "namun harus dipahami bahwa _high accuracy_ sebagian disebabkan oleh sifat "
        "rule-based labeling, bukan karena model menangkap pola yang kompleks."
    )
    lines.append("")
    lines.append("### Data Sintetis")
    lines.append(
        "Seluruh data dihasilkan oleh `src/make_dummy_data.py` dan bukan data asli ROKKUS. "
        "Distribusi stok, pola musiman, dan variabilitas di data nyata mungkin berbeda "
        "secara signifikan. Lakukan retraining dengan data asli sebelum deployment."
    )
    lines.append("")
    lines.append("### Split Berbasis Waktu")
    lines.append(
        "Evaluasi menggunakan split waktu (train = awal, test = akhir) untuk "
        "menghindari kebocoran temporal. Ini lebih konservatif dari random split "
        "dan lebih merepresentasikan performa saat deploy ke produksi."
    )
    lines.append("")

    md_path = report_dir / "model_comparison.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(f"📝 Markdown report disimpan → {md_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Jalankan via train.py; ini entry point untuk debugging evaluasi saja
    print("Gunakan: python src/train.py  untuk melatih dan mengevaluasi semua model.")
