# src/loader.py
import json
from pathlib import Path
import joblib
import streamlit as st

ART_DIR = Path(__file__).resolve().parent.parent / "artifacts"


@st.cache_resource(show_spinner="Memuat model...")
def load_model():
    return joblib.load(ART_DIR / "model_debit_sungai.joblib")


@st.cache_data
def load_meta() -> dict:
    with open(ART_DIR / "model_meta.json", encoding="utf-8") as f:
        return json.load(f)
