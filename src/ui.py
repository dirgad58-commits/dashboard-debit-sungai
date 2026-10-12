# src/ui.py
from pathlib import Path
import streamlit as st

CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.css"


def _html(block: str) -> str:
    """Hilangkan indentasi agar Markdown tidak menganggap HTML sebagai blok kode."""
    return "".join(line.strip() for line in block.splitlines())


def render(block: str) -> None:
    st.markdown(_html(block), unsafe_allow_html=True)


def load_css() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)


def hero(loc: str, subtitle: str) -> None:
    render(f"""
    <div class="hero">
      <div>
        <h1>🌊 Prediksi Debit Sungai</h1>
        <p>{subtitle}</p>
      </div>
      <div class="hero-chip">📍 Stasiun {loc}</div>
    </div>
    """)


def kpi_row(cards: list[dict]) -> None:
    """cards: [{label, value, unit, sub, icon, accent}, ...]"""
    items = ""
    for c in cards:
        items += f"""
        <div class="kpi" style="--accent:{c.get('accent', '#0b6efd')}">
          <div class="kpi-top">
            <span class="kpi-label">{c['label']}</span>
            <span class="kpi-icon">{c.get('icon', '')}</span>
          </div>
          <div class="kpi-value">{c['value']}<span class="kpi-unit">{c.get('unit', '')}</span></div>
          <div class="kpi-sub">{c.get('sub', '')}</div>
        </div>
        """
    render(f'<div class="kpi-grid">{items}</div>')


WARNA_HEX = {"green": "#16a34a", "orange": "#f59e0b", "red": "#dc2626"}


def status_banner(hasil: dict) -> None:
    render(f"""
    <div class="status {hasil['warna']}">
      <span class="dot"></span>
      <div>{hasil['status']}
        <small>Prediksi {hasil['prediksi_m3s']:.2f} m³/s untuk
        {hasil['tanggal_prediksi']:%d %B %Y} — {hasil['rasio']*100:.0f}% dari ambang P90
        ({hasil['ambang_p90']:.2f} m³/s)</small>
      </div>
    </div>
    """)


def gauge(hasil: dict) -> None:
    lebar = min(hasil["rasio"] * 100, 100)
    render(f"""
    <div class="gauge-card">
      <div class="gauge-head">
        <span>Posisi prediksi terhadap ambang banjir (P90)</span>
        <span>{hasil['rasio']*100:.0f}%</span>
      </div>
      <div class="gauge-track">
        <div class="gauge-fill" style="width:{lebar:.1f}%; --fill:{WARNA_HEX[hasil['warna']]}"></div>
        <div class="gauge-mark"></div>
      </div>
      <div class="gauge-scale"><span>0</span><span>Ambang P90 = {hasil['ambang_p90']:.2f} m³/s</span></div>
    </div>
    """)


def section(title: str) -> None:
    render(f'<div class="section-title">{title}</div>')


def footer(text: str) -> None:
    render(f'<div class="app-footer">{text}</div>')
