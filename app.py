# app.py
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import ui
from src.features import LOCATIONS
from src.loader import load_meta, load_model
from src.predict import predict_history, predict_next_day

st.set_page_config(page_title="Prediksi Debit Sungai", page_icon="🌊", layout="wide")
ui.load_css()

model = load_model()
meta = load_meta()


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"])


def style_fig(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        height=height, template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#0f2742"),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", y=1.12, x=0),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e2e8f0", title="Debit (m³/s)")
    return fig


# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 🌊 Pengaturan")
loc = st.sidebar.selectbox("📍 Lokasi stasiun", LOCATIONS)
sumber = st.sidebar.radio("📁 Sumber data", ["CSV bawaan", "Upload CSV"])

if sumber == "Upload CSV":
    up = st.sidebar.file_uploader("Upload CSV (date, loc, discharge_m3s, rain_mm)", type="csv")
    if up is None:
        st.info("Silakan upload CSV di sidebar.")
        st.stop()
    data = pd.read_csv(up, parse_dates=["date"])
else:
    data = load_data("data/riwayat_debit_hujan.csv")

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Model:** {meta['model_name']}  \n"
    f"**Dilatih:** {meta['trained_at'][:10]}  \n"
    f"**R²:** {meta['test_metrics']['R2 Score']}"
)

df_loc = data[data["loc"] == loc].sort_values("date")
if df_loc.empty:
    st.warning(f"Tidak ada data untuk lokasi {loc}.")
    st.stop()

# ---------------- HERO ----------------
ui.hero(loc, f"Prediksi debit hari berikutnya · data {meta['data_period']['start']} "
             f"s/d {meta['data_period']['end']}")

tab1, tab2, tab3 = st.tabs(["📈 Prediksi", "📊 Evaluasi Model", "ℹ️ Tentang"])

# ---------------- TAB 1: PREDIKSI ----------------
with tab1:
    try:
        hasil = predict_next_day(model, meta, df_loc, loc)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    aktual = df_loc["discharge_m3s"].iloc[-1]
    selisih = hasil["prediksi_m3s"] - aktual
    arah = "▲" if selisih >= 0 else "▼"

    ui.kpi_row([
        dict(label="Debit terakhir", value=f"{aktual:.2f}", unit="m³/s",
             sub=f"Per {df_loc['date'].iloc[-1]:%d %b %Y}", icon="💧", accent="#0b6efd"),
        dict(label=f"Prediksi {hasil['tanggal_prediksi']:%d %b}", value=f"{hasil['prediksi_m3s']:.2f}",
             unit="m³/s", sub=f"{arah} {abs(selisih):.2f} dari hari ini", icon="🔮", accent="#0ea5a4"),
        dict(label="Ambang banjir P90", value=f"{hasil['ambang_p90']:.2f}", unit="m³/s",
             sub="Persentil ke-90 data latih", icon="🚧", accent="#f59e0b"),
        dict(label="Rasio terhadap ambang", value=f"{hasil['rasio']*100:.0f}", unit="%",
             sub=hasil["status"].split("—")[0].strip(), icon="📏",
             accent=ui.WARNA_HEX[hasil["warna"]]),
    ])

    ui.status_banner(hasil)
    ui.gauge(hasil)

    # --- grafik aktual vs prediksi ---
    ui.section("Debit aktual vs prediksi")
    with st.container(border=True):
        hist = predict_history(model, meta, df_loc, loc)
        n_hari = st.slider("Tampilkan N hari terakhir", 14, min(365, len(df_loc)), min(60, len(df_loc)))
        plot_df = df_loc.set_index("date").tail(n_hari)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["discharge_m3s"], name="Aktual",
                                 mode="lines", line=dict(color="#0b6efd", width=3),
                                 fill="tozeroy", fillcolor="rgba(11,110,253,.08)"))
        fig.add_trace(go.Scatter(x=hist.index[-n_hari:], y=hist["prediksi_hari_berikutnya"].tail(n_hari),
                                 name="Prediksi", mode="lines",
                                 line=dict(color="#0ea5a4", width=2.5, dash="dot")))
        fig.add_hline(y=hasil["ambang_p90"], line_dash="dash", line_color="#dc2626",
                      annotation_text="Ambang P90", annotation_position="top left")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    # --- curah hujan ---
    ui.section("Curah hujan harian")
    with st.container(border=True):
        figr = go.Figure(go.Bar(x=plot_df.index, y=plot_df["rain_mm"], marker_color="#38bdf8",
                                name="Hujan (mm)"))
        style_fig(figr, 280).update_yaxes(title="Hujan (mm)")
        st.plotly_chart(figr, use_container_width=True)

# ---------------- TAB 2: EVALUASI ----------------
with tab2:
    m = meta["test_metrics"]
    ui.kpi_row([
        dict(label="MAE", value=m["MAE (m3/s)"], unit="m³/s", icon="🎯", accent="#0b6efd",
             sub="Rata-rata galat absolut"),
        dict(label="RMSE", value=m["RMSE (m3/s)"], unit="m³/s", icon="📐", accent="#0ea5a4",
             sub="Sensitif terhadap galat besar"),
        dict(label="R² Score", value=m["R2 Score"], icon="📈", accent="#16a34a",
             sub="Variasi yang dijelaskan model"),
        dict(label="MAE (%)", value=m["MAE Pct (%)"], unit="%", icon="📊", accent="#f59e0b",
             sub="Galat relatif rata-rata"),
    ])

    ui.section("Feature importance")
    with st.container(border=True):
        imp = pd.Series(model.feature_importances_, index=meta["features"]).sort_values()
        figi = go.Figure(go.Bar(x=imp.values, y=imp.index, orientation="h",
                                marker_color="#0b6efd"))
        style_fig(figi, 560).update_xaxes(title="Importance")
        figi.update_yaxes(title="")
        st.plotly_chart(figi, use_container_width=True)

    ui.section("Ambang banjir P90 per lokasi")
    with st.container(border=True):
        st.dataframe(pd.DataFrame(meta["p90_thresholds_m3s"], index=["P90 (m³/s)"]).T,
                     use_container_width=True)

# ---------------- TAB 3: TENTANG ----------------
with tab3:
    ui.section("Tentang model")
    with st.container(border=True):
        st.markdown(f"""
**Target prediksi:** `{meta['target_variable']}` (hasil di-invers dengan `expm1`).

**Fitur ({len(meta['features'])}):** {", ".join(meta["features"])}

**Catatan:** Prediksi bersifat pendukung keputusan, bukan pengganti peringatan dini resmi.
""")

ui.footer("Dashboard Prediksi Debit Sungai · dibangun dengan Streamlit")
