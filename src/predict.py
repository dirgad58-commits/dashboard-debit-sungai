# src/predict.py
import numpy as np
import pandas as pd

from .features import build_features


def predict_next_day(model, meta: dict, df_loc: pd.DataFrame, loc: str) -> dict:
    feats = build_features(df_loc, loc, meta["features"]).dropna()
    if feats.empty:
        raise ValueError("Riwayat data belum cukup (butuh minimal ±8 hari berurutan).")

    x_last = feats.iloc[[-1]]                       # baris terbaru
    pred_log = model.predict(x_last)[0]
    pred_q = float(np.expm1(pred_log))              # kembalikan dari log1p

    thr = meta["p90_thresholds_m3s"][loc]
    rasio = pred_q / thr

    if rasio >= 1.0:
        status, warna = "WASPADA — di atas ambang P90", "red"
    elif rasio >= 0.8:
        status, warna = "SIAGA — mendekati ambang P90", "orange"
    else:
        status, warna = "NORMAL", "green"

    return {
        "tanggal_basis": feats.index[-1],
        "tanggal_prediksi": feats.index[-1] + pd.Timedelta(days=1),
        "prediksi_m3s": pred_q,
        "ambang_p90": thr,
        "rasio": rasio,
        "status": status,
        "warna": warna,
    }


def predict_history(model, meta: dict, df_loc: pd.DataFrame, loc: str) -> pd.DataFrame:
    """Prediksi untuk semua tanggal historis (untuk grafik aktual vs prediksi)."""
    feats = build_features(df_loc, loc, meta["features"]).dropna()
    pred = np.expm1(model.predict(feats))
    out = pd.DataFrame({"prediksi_hari_berikutnya": pred}, index=feats.index)
    out.index = out.index + pd.Timedelta(days=1)    # geser: prediksi untuk H+1
    return out
