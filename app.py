# app.py - Hydrological Streamlit Dashboard (Professional Enterprise Edition)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from src import ui
from src.loader import load_gbr_model, load_thresholds, load_features_schema, load_model_metadata, load_dataset
from src.predict import predict_from_user_inputs

# Configure Streamlit Page
st.set_page_config(
    page_title="Sistem Monitoring & Prediksi Debit Aliran Sungai",
    layout="wide",
    initial_sidebar_state="expanded"
)
ui.load_theme()

# Load Core Artifacts
model = load_gbr_model()
thresholds = load_thresholds()
schema = load_features_schema()
metadata = load_model_metadata()
feature_cols = schema["feature_names"]

# ------------------------------------------------------------------------------
# SIDEBAR: NAVIGATION MENU
# ------------------------------------------------------------------------------
st.sidebar.markdown("""
<div style="padding: 10px 0 16px 0; border-bottom: 1px solid #1e3a5f; margin-bottom: 12px;">
  <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff; letter-spacing: -0.01em;">HYDRO-INTELLIGENCE</div>
  <div style="font-size: 0.78rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px;">DAS Flood Early Warning System</div>
</div>
""", unsafe_allow_html=True)

MENU_OPTIONS = [
    "1. Simulasi Prediksi Mandiri",
    "2. Akses Data & Database MySQL",
    "3. Analitik Tren Hidrologi",
    "4. Arsitektur Model & Kamus Fitur"
]
selected_menu = st.sidebar.radio("NAVIGASI DASHBOARD", MENU_OPTIONS)

st.sidebar.markdown("---")
city_names = list(thresholds.keys())
selected_city = st.sidebar.selectbox("LOKASI STASIUN DAS", city_names, index=0)
city_info = thresholds[selected_city]

st.sidebar.markdown("""
<div style="font-size: 0.75rem; color: #cbd5e1; line-height: 1.5; margin-top: 10px;">
  <strong>INFO STASIUN:</strong><br>
  - Kode: <code>{loc_id}</code><br>
  - Elevasi: {elev} m dpl<br>
  - Ambang P90: {p90:.2f} m³/s
</div>
""".format(
    loc_id=city_info["location_id"],
    elev=city_info["elevation_m"],
    p90=city_info["threshold_p90_m3s"]
), unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# MENU 1: SIMULASI PREDIKSI MANDIRI (INPUT USER INTERAKTIF)
# ------------------------------------------------------------------------------
if selected_menu == "1. Simulasi Prediksi Mandiri":
    ui.header(
        "Simulasi Prediksi Debit Aliran Sungai H+1",
        f"Stasiun Pengamatan {selected_city} — Estimasi Debit Esok Hari Berdasarkan Input Parameter Hidrometeorologis"
    )

    st.markdown("""
    Modul ini mengizinkan operator untuk menginputkan kondisi fisik debit eksisting dan dinamika curah hujan lokal 
    untuk menghitung debit esok hari secara deterministik menggunakan model **Gradient Boosting Regressor**.
    """)

    with st.form("simulation_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("<strong>Kondisi Aliran Sungai (Debit m³/s)</strong>", unsafe_allow_html=True)
            def_q = float(city_info["debit_normal_mean"])
            in_q_lag1 = st.number_input("Debit Sungai Hari Ini (m³/s)", min_value=0.0, max_value=2000.0, value=round(def_q, 2), step=0.5)
            in_q_lag2 = st.number_input("Debit Sungai Kemarin (Lag-2, m³/s)", min_value=0.0, max_value=2000.0, value=round(def_q * 0.95, 2), step=0.5)
            in_q_lag3 = st.number_input("Debit 2 Hari Lalu (Lag-3, m³/s)", min_value=0.0, max_value=2000.0, value=round(def_q * 0.92, 2), step=0.5)
            in_q_roll7 = st.number_input("Rata-rata Bergerak Debit 7 Hari (m³/s)", min_value=0.0, max_value=2000.0, value=round(def_q * 0.96, 2), step=0.5)

        with col2:
            st.markdown("<strong>Curah Hujan Harian (Rainfall mm)</strong>", unsafe_allow_html=True)
            in_rain = st.number_input("Curah Hujan Hari Ini (mm)", min_value=0.0, max_value=500.0, value=25.0, step=1.0)
            in_rain_lag1 = st.number_input("Curah Hujan Kemarin (Lag-1, mm)", min_value=0.0, max_value=500.0, value=15.0, step=1.0)
            in_rain_lag2 = st.number_input("Curah Hujan 2 Hari Lalu (Lag-2, mm)", min_value=0.0, max_value=500.0, value=8.0, step=1.0)

        with col3:
            st.markdown("<strong>Akumulasi Beban Hujan & Kalender</strong>", unsafe_allow_html=True)
            in_rain_roll3 = st.number_input("Akumulasi Curah Hujan 3 Hari (mm)", min_value=0.0, max_value=1000.0, value=48.0, step=2.0)
            in_rain_roll7 = st.number_input("Akumulasi Curah Hujan 7 Hari (mm)", min_value=0.0, max_value=1500.0, value=95.0, step=5.0)
            in_month = st.selectbox("Bulan Pengamatan", list(range(1, 13)), index=9, format_func=lambda m: ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"][m-1])

        submit_btn = st.form_submit_button("JALANKAN PREDIKSI DEBIT H+1", use_container_width=True)

    if submit_btn:
        res = predict_from_user_inputs(
            model=model,
            city_threshold_data=city_info,
            discharge_lag1=in_q_lag1,
            discharge_lag2=in_q_lag2,
            discharge_lag3=in_q_lag3,
            discharge_roll7=in_q_roll7,
            rain_mm=in_rain,
            rain_lag1=in_rain_lag1,
            rain_lag2=in_rain_lag2,
            rain_roll3=in_rain_roll3,
            rain_roll7=in_rain_roll7,
            month=in_month,
            feature_order=feature_cols
        )

        ui.section_title("Hasil Evaluasi Prediksi Model")
        ui.alert_banner(res["status"], res["title"], res["description"])

        diff_q = res["prediction_m3s"] - in_q_lag1
        diff_str = f"+{diff_q:.2f} m³/s" if diff_q >= 0 else f"{diff_q:.2f} m³/s"

        ui.metric_row([
            {"label": "Debit Hari Ini (Input)", "value": f"{in_q_lag1:.2f}", "unit": "m³/s", "sub": "Kondisi observasi saat ini"},
            {"label": "Prediksi Debit H+1", "value": f"{res['prediction_m3s']:.2f}", "unit": "m³/s", "sub": f"Tren perubahan: {diff_str}"},
            {"label": "Ambang Batas Siaga P90", "value": f"{res['threshold_p90']:.2f}", "unit": "m³/s", "sub": f"DAS {selected_city}"},
            {"label": "Rasio Debit / P90", "value": f"{res['ratio']*100:.1f}", "unit": "%", "sub": f"Status: {res['status']}"}
        ])

        ui.threshold_gauge(res["prediction_m3s"], res["threshold_p90"])

        with st.expander("Lihat Rincian Vektor Fitur Yang Masuk ke Model", expanded=False):
            st.json(res["input_features"])

# ------------------------------------------------------------------------------
# MENU 2: AKSES DATA & DATABASE MYSQL
# ------------------------------------------------------------------------------
elif selected_menu == "2. Akses Data & Database MySQL":
    ui.header(
        "Akses Data Operasional & Integrasi Database",
        "Inspeksi Tabel Relasional dari Database MySQL / Repositori Data Terpadu"
    )

    col_toggle1, col_toggle2 = st.columns([1, 2])
    with col_toggle1:
        use_mysql_flag = st.checkbox("Hubungkan ke Database MySQL", value=False)
    with col_toggle2:
        mysql_input_uri = st.text_input("MySQL Connection URI", value="mysql+pymysql://root:rootpassword@localhost:3306/banjir_db")

    df_all, source_name = load_dataset(use_mysql=use_mysql_flag, mysql_uri=mysql_input_uri)

    st.info(f"Sumber Data Aktif: {source_name} | Total Baris Tercatat: {len(df_all):,} baris")

    df_city_data = df_all[df_all["loc"] == city_info["location_id"]].sort_values("date").reset_index(drop=True)

    tab_t1, tab_t2, tab_t3 = st.tabs(["Data Terpadu Stasiun Aktif", "Ringkasan Statistik", "Metadata Stasiun"])

    with tab_t1:
        st.dataframe(df_city_data[["date", "loc", "city_name", "discharge_m3s", "rain_mm"]].tail(50), use_container_width=True)
        csv_download = df_city_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="UNDUH DATASET AKTIF (CSV FORMAT)",
            data=csv_download,
            file_name=f"dataset_{city_info['location_id']}_debit_hujan.csv",
            mime="text/csv"
        )

    with tab_t2:
        st.markdown("<strong>Statistik Deskriptif Parameter Pengamatan</strong>", unsafe_allow_html=True)
        st.dataframe(df_city_data[["discharge_m3s", "rain_mm"]].describe().round(3), use_container_width=True)

    with tab_t3:
        st.markdown("<strong>Daftar 6 Titik Pengamatan DAS Nasional</strong>", unsafe_allow_html=True)
        df_loc_summary = pd.DataFrame(thresholds).T.reset_index().rename(columns={"index": "Nama Kota"})
        st.dataframe(df_loc_summary, use_container_width=True)

# ------------------------------------------------------------------------------
# MENU 3: ANALITIK TREN HIDROLOGI
# ------------------------------------------------------------------------------
elif selected_menu == "3. Analitik Tren Hidrologi":
    ui.header(
        "Analitik Tren & Dinamika Aliran Sungai",
        f"Stasiun Pengamatan {selected_city} — Analisis Deret Waktu Debit dan Korelasi Curah Hujan"
    )

    df_all, _ = load_dataset()
    df_c = df_all[df_all["loc"] == city_info["location_id"]].sort_values("date").reset_index(drop=True)

    n_days = st.slider("Rentang Hari Terakhir Ditampilkan", min_value=30, max_value=min(365, len(df_c)), value=90)
    plot_sub = df_c.tail(n_days)

    # Plot 1: Dual-Axis Time Series
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=plot_sub["date"], y=plot_sub["discharge_m3s"],
        name="Debit Sungai (m³/s)", mode="lines",
        line=dict(color="#0284c7", width=2.5)
    ))
    fig_ts.add_hline(
        y=city_info["threshold_p90_m3s"],
        line_dash="dash", line_color="#dc2626",
        annotation_text=f"Ambang P90 ({city_info['threshold_p90_m3s']:.2f} m³/s)"
    )
    fig_ts.update_layout(
        title=f"Deret Waktu Debit Aliran Sungai ({selected_city})",
        template="plotly_white",
        yaxis_title="Debit Sungai (m³/s)",
        xaxis_title="Tanggal Observasi",
        height=420,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_ts, use_container_width=True)

    # Plot 2: Curah Hujan
    fig_rain = go.Figure(go.Bar(
        x=plot_sub["date"], y=plot_sub["rain_mm"],
        name="Curah Hujan (mm)", marker_color="#38bdf8"
    ))
    fig_rain.update_layout(
        title="Fluktuasi Curah Hujan Harian",
        template="plotly_white",
        yaxis_title="Curah Hujan (mm)",
        height=260,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_rain, use_container_width=True)

# ------------------------------------------------------------------------------
# MENU 4: ARSITEKTUR MODEL & KAMUS FITUR
# ------------------------------------------------------------------------------
elif selected_menu == "4. Arsitektur Model & Kamus Fitur":
    ui.header(
        "Dokumentasi Model & Kamus Fitur",
        "Spesifikasi Teknis Algoritma Gradient Boosting Regressor (GBR) dan Schema Input"
    )

    m = metadata.get("metrics_test", {})
    ui.metric_row([
        {"label": "Algoritma Terlatih", "value": "GBR", "sub": "Ensemble Gradient Boosting", "accent": "#0284c7"},
        {"label": "Mean Absolute Error", "value": f"{m.get('MAE_m3s', 5.27):.2f}", "unit": "m³/s", "sub": "Galat absolut rata-rata", "accent": "#0369a1"},
        {"label": "Root Mean Squared Error", "value": f"{m.get('RMSE_m3s', 9.72):.2f}", "unit": "m³/s", "sub": "Penalti galat ekstrem", "accent": "#0284c7"},
        {"label": "Koefisien Determinasi R²", "value": f"{m.get('R2_Score', 0.87):.3f}", "sub": "Akurasi variansi data uji", "accent": "#16a34a"}
    ])

    ui.section_title("Kamus Fitur Input Model (15 Fitur Teknis)")
    
    feature_dict = [
        {"Fitur": "discharge_lag1", "Kategori": "Autoregresif", "Definisi": "Volume debit sungai observasi hari ini (H-0, m³/s)"},
        {"Fitur": "discharge_lag2", "Kategori": "Autoregresif", "Definisi": "Volume debit sungai observasi kemarin (H-1, m³/s)"},
        {"Fitur": "discharge_lag3", "Kategori": "Autoregresif", "Definisi": "Volume debit sungai 2 hari lalu (H-2, m³/s)"},
        {"Fitur": "discharge_roll7", "Kategori": "Inersia Aliran", "Definisi": "Rata-rata bergerak debit sungai 7 hari terakhir (m³/s)"},
        {"Fitur": "rain_mm", "Kategori": "Meteorologis", "Definisi": "Curah hujan harian terukur hari ini (mm)"},
        {"Fitur": "rain_lag1", "Kategori": "Meteorologis", "Definisi": "Curah hujan harian terukur kemarin (mm)"},
        {"Fitur": "rain_lag2", "Kategori": "Meteorologis", "Definisi": "Curah hujan harian 2 hari lalu (mm)"},
        {"Fitur": "rain_roll3", "Kategori": "Infiltrasi DAS", "Definisi": "Akumulasi curah hujan kumulatif 3 hari terakhir (mm)"},
        {"Fitur": "rain_roll7", "Kategori": "Infiltrasi DAS", "Definisi": "Akumulasi curah hujan kumulatif 7 hari terakhir (mm)"},
        {"Fitur": "elevation_m", "Kategori": "Geografis", "Definisi": "Ketinggian topografi stasiun dari permukaan laut (m dpl)"},
        {"Fitur": "latitude", "Kategori": "Geografis", "Definisi": "Koordinat lintang geografis stasiun pengamatan"},
        {"Fitur": "longitude", "Kategori": "Geografis", "Definisi": "Koordinat bujur geografis stasiun pengamatan"},
        {"Fitur": "bulan_sin", "Kategori": "Siklus Waktu", "Definisi": "Transformasi sinus siklus kalender tahunan (sin(2*pi*m/12))"},
        {"Fitur": "bulan_cos", "Kategori": "Siklus Waktu", "Definisi": "Transformasi cosinus siklus kalender tahunan (cos(2*pi*m/12))"},
        {"Fitur": "musim_hujan", "Kategori": "Klimatologis", "Definisi": "Biner indikator musim hujan monsun (1: Okt-Apr, 0: Mei-Sep)"}
    ]

    st.dataframe(pd.DataFrame(feature_dict), use_container_width=True)

    if hasattr(model, "feature_importances_"):
        ui.section_title("Peringkat Bobot Kepentingan Fitur (Feature Importance)")
        imp_series = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=True)
        fig_imp = px.bar(
            x=imp_series.values, y=imp_series.index, orientation='h',
            labels={"x": "Importance Score (Gain)", "y": "Nama Fitur"},
            color_discrete_sequence=["#0284c7"]
        )
        fig_imp.update_layout(template="plotly_white", height=450, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_imp, use_container_width=True)
