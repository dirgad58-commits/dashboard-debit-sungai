# src/features.py
import numpy as np
import pandas as pd

LOCATIONS = ["BJM", "BKS", "JKT", "PTK", "SMD", "SMG"]


def build_features(df: pd.DataFrame, loc: str, feature_cols: list[str]) -> pd.DataFrame:
    """
    df          : riwayat SATU lokasi, kolom: date, discharge_m3s, rain_mm
    loc         : kode lokasi, mis. 'BJM'
    feature_cols: daftar 21 nama fitur
    return      : DataFrame fitur per tanggal, kolom persis = feature_cols
    """
    d = df.sort_values("date").copy()
    d["date"] = pd.to_datetime(d["date"])
    q = d["discharge_m3s"]

    # --- fitur debit ---
    d["log_q"] = np.log1p(q)
    d["q_diff1"] = q.diff(1)
    d["q_roll_mean7"] = q.rolling(7).mean()
    d["q_roll_std7"] = q.rolling(7).std()
    for k in (1, 2, 3, 7):
        d[f"log_q_lag_{k}"] = d["log_q"].shift(k)

    # --- fitur hujan ---
    d["rain_lag_1"] = d["rain_mm"].shift(1)
    d["rain_lag_2"] = d["rain_mm"].shift(2)
    d["rain_sum_3d"] = d["rain_mm"].rolling(3).sum()
    d["rain_sum_7d"] = d["rain_mm"].rolling(7).sum()

    # --- fitur musiman ---
    bulan = d["date"].dt.month
    d["bulan_sin"] = np.sin(2 * np.pi * bulan / 12)
    d["bulan_cos"] = np.cos(2 * np.pi * bulan / 12)

    # --- one-hot lokasi ---
    for L in LOCATIONS:
        d[f"loc_{L}"] = 1 if L == loc else 0

    d = d.set_index("date")
    return d[feature_cols]
