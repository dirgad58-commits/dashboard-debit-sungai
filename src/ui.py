# src/ui.py - Formal Design Component Renderer (Zero Emojis)
from pathlib import Path
import streamlit as st

CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.css"


def _sanitize(html_str: str) -> str:
    return "".join(line.strip() for line in html_str.splitlines())


def render(html_str: str) -> None:
    st.markdown(_sanitize(html_str), unsafe_allow_html=True)


def load_theme() -> None:
    if CSS_PATH.exists():
        st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def header(title: str, subtitle: str, badge: str = "PRODUCTION MODEL") -> None:
    render(f"""
    <div class="app-header">
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      <div class="header-badge">{badge}</div>
    </div>
    """)


def section_title(label: str) -> None:
    render(f'<div class="section-header">{label}</div>')


def metric_row(cards: list[dict]) -> None:
    items = ""
    for c in cards:
        accent = c.get('accent', '#0284c7')
        unit = f"<span class='metric-card-unit'>{c.get('unit', '')}</span>" if c.get('unit') else ""
        sub = f"<div class='metric-card-sub'>{c.get('sub', '')}</div>" if c.get('sub') else ""
        items += f"""
        <div class="metric-card" style="--accent-bar: {accent};">
          <div class="metric-card-label">{c['label']}</div>
          <div class="metric-card-val">{c['value']}{unit}</div>
          {sub}
        </div>
        """
    render(f'<div class="metric-grid">{items}</div>')


def alert_banner(level: str, title: str, description: str) -> None:
    level = level.lower()
    if level == "critical":
        css_class = "alert-critical"
        tag_class = "tag-critical"
        tag_text = "STATUS: KRITIS / WASPADA"
    elif level == "warning":
        css_class = "alert-warning"
        tag_class = "tag-warning"
        tag_text = "STATUS: SIAGA BANJIR"
    else:
        css_class = "alert-normal"
        tag_class = "tag-normal"
        tag_text = "STATUS: NORMAL / AMAN"

    render(f"""
    <div class="alert-panel {css_class}">
      <div>
        <span class="alert-tag {tag_class}">{tag_text}</span>
        <div style="font-weight: 700; font-size: 1.05rem; margin-top: 2px;">{title}</div>
        <div style="font-size: 0.88rem; margin-top: 4px; opacity: 0.95;">{description}</div>
      </div>
    </div>
    """)


def threshold_gauge(value: float, threshold: float, label: str = "Rasio Terhadap Ambang P90") -> None:
    ratio = value / threshold if threshold > 0 else 0
    pct = min(ratio * 100, 100)
    if ratio >= 1.0:
        bar_color = "#dc2626"
    elif ratio >= 0.8:
        bar_color = "#d97706"
    else:
        bar_color = "#16a34a"

    render(f"""
    <div class="gauge-box">
      <div class="gauge-header">
        <span>{label}</span>
        <span>{ratio*100:.1f}% ({value:.2f} / {threshold:.2f} m³/s)</span>
      </div>
      <div class="gauge-track">
        <div class="gauge-bar" style="width: {pct:.1f}%; background-color: {bar_color};"></div>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #64748b; margin-top: 5px;">
        <span>0 m³/s (Normal)</span>
        <span>Ambang Kritis P90: {threshold:.2f} m³/s</span>
      </div>
    </div>
    """)
