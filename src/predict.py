# src/predict.py - Dynamic Feature Calculation & Inference
import numpy as np
import pandas as pd


def predict_from_user_inputs(
    model,
    city_threshold_data: dict,
    discharge_lag1: float,
    discharge_lag2: float,
    discharge_lag3: float,
    discharge_roll7: float,
    rain_mm: float,
    rain_lag1: float,
    rain_lag2: float,
    rain_roll3: float,
    rain_roll7: float,
    month: int,
    feature_order: list[str]
) -> dict:
    city_info = city_threshold_data
    elevation_m = float(city_info["elevation_m"])
    latitude = float(city_info["latitude"])
    longitude = float(city_info["longitude"])
    threshold_p90 = float(city_info["threshold_p90_m3s"])

    bulan_sin = float(np.sin(2 * np.pi * month / 12))
    bulan_cos = float(np.cos(2 * np.pi * month / 12))
    musim_hujan = 1 if (month >= 10 or month <= 4) else 0

    input_payload = {
        "discharge_lag1": discharge_lag1,
        "discharge_lag2": discharge_lag2,
        "discharge_lag3": discharge_lag3,
        "discharge_roll7": discharge_roll7,
        "rain_mm": rain_mm,
        "rain_lag1": rain_lag1,
        "rain_lag2": rain_lag2,
        "rain_roll3": rain_roll3,
        "rain_roll7": rain_roll7,
        "elevation_m": elevation_m,
        "latitude": latitude,
        "longitude": longitude,
        "bulan_sin": bulan_sin,
        "bulan_cos": bulan_cos,
        "musim_hujan": musim_hujan
    }

    df_sample = pd.DataFrame([input_payload])[feature_order]
    pred_discharge = float(model.predict(df_sample)[0])

    ratio = pred_discharge / threshold_p90 if threshold_p90 > 0 else 0
    if ratio >= 1.0:
        status = "CRITICAL"
        title = f"Peringatan Luapan Banjir (Debit Prediksi: {pred_discharge:.2f} m³/s)"
        desc = f"Debit diperkirakan melampaui ambang batas siaga P90 ({threshold_p90:.2f} m³/s). Diperlukan aktivasi protokol darurat evakuasi dan pengoperasian pompa retensi."
    elif ratio >= 0.8:
        status = "WARNING"
        title = f"Siaga Waspada Peningkatan Debit (Debit Prediksi: {pred_discharge:.2f} m³/s)"
        desc = f"Debit berada pada {ratio*100:.1f}% dari ambang batas siaga P90 ({threshold_p90:.2f} m³/s). Waspadai kenaikan muka air dalam 24 jam ke depan."
    else:
        status = "NORMAL"
        title = f"Kondisi Aliran Sungai Normal (Debit Prediksi: {pred_discharge:.2f} m³/s)"
        desc = f"Debit berada dalam batas kapasitas aman DAS ({ratio*100:.1f}% dari ambang P90: {threshold_p90:.2f} m³/s). Operasi sungai berjalan standar."

    return {
        "prediction_m3s": pred_discharge,
        "threshold_p90": threshold_p90,
        "ratio": ratio,
        "status": status,
        "title": title,
        "description": desc,
        "input_features": input_payload
    }
