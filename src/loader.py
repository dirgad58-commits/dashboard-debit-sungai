# src/loader.py - Data & Model Artifact Loader
import json
import pickle
import os
from pathlib import Path
import pandas as pd
import streamlit as st
import sqlalchemy as sa
from sqlalchemy import create_engine, text

ART_DIR = Path(__file__).resolve().parent.parent / "artifacts"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_resource(show_spinner="Memuat model inferensi...")
def load_gbr_model():
    model_path = ART_DIR / "flood_discharge_gbr.pkl"
    if not model_path.exists():
        model_path = ART_DIR / "model_debit_sungai.joblib"
        import joblib
        return joblib.load(model_path)
    with open(model_path, "rb") as f:
        return pickle.load(f)


@st.cache_data
def load_thresholds() -> dict:
    thr_path = ART_DIR / "city_flood_thresholds.json"
    with open(thr_path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_features_schema() -> dict:
    schema_path = ART_DIR / "features_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_model_metadata() -> dict:
    meta_path = ART_DIR / "model_metadata.json"
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_dataset(use_mysql: bool = False, mysql_uri: str = "mysql+pymysql://root:rootpassword@localhost:3306/banjir_db"):
    if use_mysql:
        try:
            engine = create_engine(mysql_uri)
            with engine.connect() as conn:
                df_dis = pd.read_sql("SELECT * FROM river_discharge", conn)
                df_rain = pd.read_sql("SELECT * FROM rainfall_daily", conn)
                df_loc = pd.read_sql("SELECT * FROM locations", conn)
                df_merge = pd.merge(df_dis, df_rain, on=["location_id", "obs_date"])
                df_merge = pd.merge(df_merge, df_loc, on="location_id")
                df_merge.rename(columns={"obs_date": "date", "location_id": "loc"}, inplace=True)
                df_merge["date"] = pd.to_datetime(df_merge["date"])
                return df_merge, "MySQL (Connected)"
        except Exception as e:
            pass  # Fallback to CSV

    csv_path = DATA_DIR / "riwayat_debit_hujan.csv"
    df = pd.read_csv(csv_path, parse_dates=["date"])
    loc_path = ART_DIR / "locations.csv"
    if loc_path.exists():
        df_loc = pd.read_csv(loc_path)
        df = pd.merge(df, df_loc, left_on="loc", right_on="location_id", how="left")
    return df, "CSV File (Local Storage)"
