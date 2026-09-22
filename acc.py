import streamlit as st
import pandas as pd
import numpy as np
import json
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


# ============================================================
# Constants
# ============================================================
SOURCE_URL = "https://www.data.gov.qa/explore/dataset/accident/information/"
SOURCE_LABEL = "Ministry of Interior · Open Data Portal"

DARK_MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
LIGHT_MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"


# ============================================================
# Arabic → English translation maps
# ============================================================
SEVERITY_MAP = {
    "اﺻﺎﺑﺎت ﺑﺳﻳطة": "Minor injury",
    "ﺣﺎدث ﺑﺳﻳط": "Minor accident",
    "اﺻﺎﺑﺎت ﻣﺗوﺳطﺔ": "Moderate injury",
    "اﺻﺎﺑﺎت ﺑﻟﻳﻐﺔ": "Severe injury",
    "إﺻﺎﺑﺔ ﺑﺎﻟﻐﺔ": "Severe injury",
    "وﻓﺎة": "Death",
    "وﻓﻳﺎت": "Death",
    "وﻓﺎة و اﺻﺎﺑﺎت": "Death and injuries",
    "اﺻﺎﺑﺔ ﺑﺳﻳطﺔ": "Minor injury",
    "اﺻﺎﺑﺔ ﻣﺗوﺳطﺔ": "Moderate injury",
    "اﺻﺎﺑﺔ ﺑﻟﻳﻐﺔ": "Severe injury",
}

NATURE_MAP = {
    "ﺗﺻﺎدم ﻣﻊ ﻣﺷﺎة": "Collision with pedestrian",
    "ﺗﺻﺎدم ﻣرﻛﺑﺗﻳن": "Collision (2 vehicles)",
    "ﺗﺻﺎدم اﻛﺛر ﻣن ﻣرﻛﺑﺗﻳن": "Collision (3+ vehicles)",
    "ﻟﻳس ﺑﺣﺎدث ﺗﺻﺎدم": "Non-collision incident",
    "اﺻطدام": "Collision",
    "اﻧﻗﻼب": "Rollover",
    "دﻫس": "Run-over",
    "ﺳﻘوط ﻣن ﻣرﻛﺑﺔ": "Fall from vehicle",
}


def _translate(series: pd.Series, mapping: dict) -> pd.Series:
    stripped = series.astype(str).str.strip()
    translated = stripped.map(mapping)
    return translated.fillna(stripped)


# ============================================================
# Themes
# ============================================================
DARK = {
    "name": "dark",
    "bg_gradient": (
        "radial-gradient(circle at 15% 10%, rgba(255,0,255,0.08), transparent 45%),"
        "radial-gradient(circle at 85% 5%, rgba(0,255,255,0.07), transparent 45%),"
        "#0a0a0a"
    ),
    "text": "#f0f0f0",
    "text_muted": "#a0a0a0",
    "text_dim": "#6a6a6a",
    "panel": "rgba(255,255,255,0.045)",
    "panel_hover": "rgba(0,255,255,0.06)",
    "panel_border": "rgba(255,255,255,0.08)",
    "panel_hover_border": "rgba(0,255,255,0.28)",
    "accent1": "#00FFFF",
    "accent2": "#FF00FF",
    "accent3": "#FF4466",
    "title_gradient": "linear-gradient(90deg, #00FFFF 0%, #FF00FF 60%, #FF3355 100%)",
    "map_style": DARK_MAP_STYLE,
    "map_color_low":  (0, 220, 255, 120),
    "map_color_mid":  (255, 0, 255, 220),
    "map_color_high": (255, 60, 0, 200),
    "map_zero":       (40, 40, 40, 30),
    "map_line":       (90, 90, 90, 180),
    "map_highlight":  (0, 255, 255, 100),
    "legend_gradient": "linear-gradient(90deg, #00dcdc 0%, #ff00ff 50%, #ff2222 100%)",
    "chart_grid": "rgba(255,255,255,0.08)",
    "chart_palette": ["#00FFFF", "#FF00FF", "#FF4466", "#7a4cff", "#39FF14", "#FFA500"],
    "select_bg": "rgba(255,255,255,0.05)",
    "select_text": "#f0f0f0",
    "select_border": "rgba(0,255,255,0.25)",
    "select_border_hover": "rgba(0,255,255,0.6)",
    "toggle_accent": "#00FFFF",
}

LIGHT = {
    "name": "light",
    "bg_gradient": (
        "radial-gradient(circle at 15% 10%, rgba(128,0,32,0.05), transparent 45%),"
        "radial-gradient(circle at 85% 5%, rgba(184,155,94,0.10), transparent 45%),"
        "#FAF7F2"
    ),
    "text": "#1a1a1a",
    "text_muted": "#555555",
    "text_dim": "#888888",
    "panel": "#ffffff",
    "panel_hover": "#FDF8F0",
    "panel_border": "rgba(128,0,32,0.12)",
    "panel_hover_border": "rgba(128,0,32,0.35)",
    "accent1": "#800020",
    "accent2": "#B89B5E",
    "accent3": "#5C0A1F",
    "title_gradient": "linear-gradient(90deg, #800020 0%, #B89B5E 100%)",
    "map_style": LIGHT_MAP_STYLE,
    "map_color_low":  (248, 243, 235, 80),
    "map_color_mid":  (200, 160, 90, 190),
    "map_color_high": (128, 0, 32, 230),
    "map_zero":       (235, 230, 220, 60),
    "map_line":       (128, 0, 32, 100),
    "map_highlight":  (128, 0, 32, 120),
    "legend_gradient": "linear-gradient(90deg, #F8F3EB 0%, #C8A05A 50%, #800020 100%)",
    "chart_grid": "rgba(128,0,32,0.10)",
    "chart_palette": ["#800020", "#C8A05A", "#5C0A1F", "#8B5A2B", "#3D2B1F", "#A67B5B"],
    "select_bg": "#ffffff",
    "select_text": "#1a1a1a",
    "select_border": "rgba(128,0,32,0.25)",
    "select_border_hover": "rgba(128,0,32,0.7)",
    "toggle_accent": "#800020",
}


# ============================================================
# Main dashboard
# ============================================================
class QatarAccidentsStreamlit:

    def __init__(self,
                 accidents_file: str = "facc.csv",
                 polygons_file: str = "qatar_zones_polygons.json"):
        self.accidents_file = accidents_file
        self.polygons_file = polygons_file
        self.df = None
        self.zones_data = None
        self.zone_names = self._load_zone_names()
        self.load_error = None
        self.load_data()

    def _load_zone_names(self) -> dict:
        try:
            with open("zone_names.json") as f:
                return json.load(f)
        except Exception:
            return {}

    # ------------------------------------------------------------
    def load_data(self) -> None:
        p = Path(self.accidents_file)
        if not p.is_file():
            self.load_error = f"`{self.accidents_file}` not found."
            return
        if p.stat().st_size == 0:
            self.load_error = f"`{self.accidents_file}` is empty."
            return

        try:
            self.df = pd.read_csv(self.accidents_file, skipinitialspace=True)
        except pd.errors.EmptyDataError:
            self.load_error = f"`{self.accidents_file}` has no parseable columns."
            return
        except Exception as e:
            self.load_error = f"Failed to read `{self.accidents_file}`: {e}"
            return

        if self.df.empty:
            self.load_error = f"`{self.accidents_file}` has 0 rows."
            return

        if "ZONE" in self.df.columns:
            zone_numeric = pd.to_numeric(
                self.df["ZONE"].astype(str).str.strip(), errors="coerce"
            )
            self.df["ZONE"] = np.where(
                zone_numeric.notna(),
                zone_numeric.fillna(0).astype(int).astype(str),
                "Unknown",
            )

        if "ACCIDENT_YEAR" in self.df.columns:
            self.df["ACCIDENT_YEAR"] = pd.to_numeric(
                self.df["ACCIDENT_YEAR"], errors="coerce"
            )
            self.df = self.df.dropna(subset=["ACCIDENT_YEAR"])
            self.df["ACCIDENT_YEAR"] = self.df["ACCIDENT_YEAR"].astype(int)

        if "ACCIDENT_TIME" in self.df.columns:
            self.df["HOUR"] = (
                self.df["ACCIDENT_TIME"].astype(str)
                .str.extract(r"(\d+)", expand=False)
                .astype(float)
            )

        if "DEATH_COUNT" in self.df.columns:
            self.df["DEATH_COUNT"] = pd.to_numeric(
                self.df["DEATH_COUNT"], errors="coerce"
            ).fillna(0).astype(int)

        if "ACCIDENT_SEVERITY" in self.df.columns:
            self.df["SEVERITY_EN"] = _translate(self.df["ACCIDENT_SEVERITY"], SEVERITY_MAP)
        if "ACCIDENT_NATURE" in self.df.columns:
            self.df["NATURE_EN"] = _translate(self.df["ACCIDENT_NATURE"], NATURE_MAP)

        if Path(self.polygons_file).is_file():
            try:
                with open(self.polygons_file) as f:
                    self.zones_data = json.load(f)
            except Exception as e:
                st.warning(f"Could not load polygons: {e}")

    # ------------------------------------------------------------
    def _interpolate_color(self, t: float, theme: dict) -> list:
        t = max(0.0, min(1.0, t))
        low = theme["map_color_low"]
        mid = theme["map_color_mid"]
        high = theme["map_color_high"]
        if t <= 0.5:
            u = t / 0.5
            return [int(low[i] + (mid[i] - low[i]) * u) for i in range(4)]
        u = (t - 0.5) / 0.5
        return [int(mid[i] + (high[i] - mid[i]) * u) for i in range(4)]

    # ------------------------------------------------------------
    def build_geojson(self, year: int, theme: dict) -> dict:
        if self.df is None or self.zones_data is None:
            return {"type": "FeatureCollection", "features": []}

        year_data = self.df[self.df["ACCIDENT_YEAR"] == year]
        zone_counts = year_data["ZONE"].value_counts().to_dict()
        counts = sorted(zone_counts.values(), reverse=True)
        max_count = counts[0] if counts else 1

        features = []
        for zone_id, z in self.zones_data.items():
            count = int(zone_counts.get(zone_id, 0))
            if count == 0:
                color = list(theme["map_zero"])
            else:
                t = (count / max_count) ** 0.5
                color = self._interpolate_color(t, theme)

            coords = [[p["lng"], p["lat"]] for p in z["coordinates"]]
            features.append({
                "type": "Feature",
                "properties": {
                    "zone_id": zone_id,
                    "name": self.zone_names.get(zone_id, f"Zone {zone_id}"),
                    "count": count,
                    "color": color,
                },
                "geometry": {"type": "Polygon", "coordinates": [coords]},
            })
        return {"type": "FeatureCollection", "features": features}

    # ------------------------------------------------------------
    def create_map(self, year: int, theme: dict) -> pdk.Deck:
        geojson = self.build_geojson(year, theme)

        layer = pdk.Layer(
            "GeoJsonLayer",
            data=geojson,
            get_fill_color="properties.color",
            get_line_color=list(theme["map_line"]),
            get_line_width=1.2,
            line_width_min_pixels=1,
            pickable=True,
            auto_highlight=True,
            highlight_color=list(theme["map_highlight"]),
            filled=True,
            stroked=True,
        )

        view_state = pdk.ViewState(
            latitude=25.2867, longitude=51.5333,
            zoom=10.6, pitch=0, bearing=0,
        )

        return pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style=theme["map_style"],
            tooltip={
                "html": "<b>{name}</b><br/>Accidents: <b>{count}</b>",
                "style": {
                    "backgroundColor": theme["panel"],
                    "color": theme["accent1"],
                    "fontFamily": "Space Grotesk, sans-serif",
                    "borderRadius": "8px",
                    "padding": "8px 12px",
                    "border": f"1px solid {theme['panel_border']}",
                },
            },
        )

    # ------------------------------------------------------------
    def calculate_metrics(self) -> dict:
        if self.df is None or self.df.empty:
            return {"annual_avg": 0, "total_deaths": 0,
                    "pedestrian_deaths": 0, "total_accidents": 0}

        if "ACCIDENT_YEAR" in self.df.columns:
            recent = self.df[self.df["ACCIDENT_YEAR"] >= 2020]
            n_years = recent["ACCIDENT_YEAR"].nunique()
            annual_avg = len(recent) / n_years if n_years else 0
        else:
            annual_avg = 0

        total_deaths = int(self.df["DEATH_COUNT"].sum()) \
            if "DEATH_COUNT" in self.df.columns else 0

        if "ACCIDENT_NATURE" in self.df.columns and "DEATH_COUNT" in self.df.columns:
            nature = self.df["ACCIDENT_NATURE"].astype(str)
            mask = (
                nature.str.contains("PEDESTRIAN", case=False, na=False)
                | nature.str.contains("ﻣﺷﺎة", na=False)
                | nature.str.contains("ﻣﺷﺎه", na=False)
            )
            ped_deaths = int(self.df.loc[mask, "DEATH_COUNT"].sum())
        else:
            ped_deaths = 0

        return {
            "annual_avg": round(annual_avg, 1),
            "total_deaths": total_deaths,
            "pedestrian_deaths": ped_deaths,
            "total_accidents": len(self.df),
        }

    @staticmethod
    def format_number(num: float) -> str:
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        if num >= 1_000:
            return f"{num / 1_000:.1f}K"
        return f"{num:,.0f}"

    # ============================================================
    # CSS
    # ============================================================
    def _inject_css(self, t: dict) -> None:
        st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

        :root {{
            --bg:                 {t["bg_gradient"]};
            --text:               {t["text"]};
            --text-muted:         {t["text_muted"]};
            --text-dim:           {t["text_dim"]};
            --panel:              {t["panel"]};
            --panel-hover:        {t["panel_hover"]};
            --panel-border:       {t["panel_border"]};
            --panel-hover-border: {t["panel_hover_border"]};
            --accent1:            {t["accent1"]};
            --accent2:            {t["accent2"]};
            --accent3:            {t["accent3"]};
            --select-bg:          {t["select_bg"]};
            --select-text:        {t["select_text"]};
            --select-border:      {t["select_border"]};
            --select-border-hover:{t["select_border_hover"]};
            --toggle-accent:      {t["toggle_accent"]};
        }}

        html, body, [class*="css"], .stApp, .stMarkdown, .stMetric,
        button, input, select, textarea {{
            font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}

        .stApp {{ background: var(--bg); color: var(--text); }}

        #MainMenu, footer, header {{ visibility: hidden; }}
        .block-container {{ padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1400px; }}

        /* ---- Masthead ---- */
        .hero-title {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 3.4rem;
            font-weight: 700;
            letter-spacing: -0.045em;
            background: {t["title_gradient"]};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            line-height: 1;
        }}
        .hero-sub {{
            color: var(--text-muted);
            font-size: 1.05rem;
            margin-top: 0.3rem;
            margin-bottom: 0.4rem;
            font-weight: 400;
        }}
        .source-line {{
            color: var(--text-dim);
            font-size: 0.78rem;
            letter-spacing: 0.02em;
            margin-bottom: 2rem;
        }}
        .source-line a {{
            color: var(--text-dim);
            text-decoration: none;
            border-bottom: 1px dotted var(--text-dim);
        }}
        .source-line a:hover {{
            color: var(--accent1);
            border-bottom-color: var(--accent1);
        }}

        /* ---- Metric cards ---- */
        .metric-card {{
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 14px;
            padding: 20px 22px;
            height: 100%;
            transition: all .25s ease;
        }}
        .metric-card:hover {{
            background: var(--panel-hover);
            border-color: var(--panel-hover-border);
            transform: translateY(-2px);
        }}
        .metric-label {{
            color: var(--text-muted);
            font-size: 0.72rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 10px;
        }}
        .metric-value {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.05rem;
            font-weight: 600;
            line-height: 1;
            color: var(--text);
        }}
        .metric-accent-1 {{ color: var(--accent1); }}
        .metric-accent-2 {{ color: var(--accent2); }}
        .metric-accent-3 {{ color: var(--accent3); }}
        .metric-sub {{
            color: var(--text-dim);
            font-size: 0.68rem;
            margin-top: 10px;
            text-transform: uppercase;
            letter-spacing: 0.09em;
        }}

        /* ---- Section title ---- */
        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text);
            margin: 0;
            letter-spacing: -0.015em;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section-title::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(180deg, var(--accent1), var(--accent2));
            border-radius: 2px;
        }}

        /* ---- Selectbox ---- */
        div[data-baseweb="select"] > div {{
            background-color: var(--select-bg) !important;
            border-color: var(--select-border) !important;
            border-radius: 10px !important;
            color: var(--select-text) !important;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace !important;
        }}
        div[data-baseweb="select"] > div:hover {{
            border-color: var(--select-border-hover) !important;
        }}
        div[data-baseweb="select"] * {{
            color: var(--select-text) !important;
        }}

        /* ---- Toggle ---- */
        div[data-testid="stToggle"] label {{
            color: var(--text-muted) !important;
            font-size: 0.85rem !important;
        }}
        div[data-testid="stToggle"] div[role="checkbox"] {{
            border-color: var(--toggle-accent) !important;
        }}
        div[data-testid="stToggle"] div[role="checkbox"][aria-checked="true"] {{
            background-color: var(--toggle-accent) !important;
            border-color: var(--toggle-accent) !important;
        }}

        /* ---- Zone cards ---- */
        .zone-card {{
            display: grid;
            grid-template-columns: 26px 1fr auto;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            margin-bottom: 8px;
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 10px;
            transition: all .2s ease;
        }}
        .zone-card:hover {{
            background: var(--panel-hover);
            border-color: var(--panel-hover-border);
            transform: translateX(3px);
        }}
        .zone-rank {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-dim);
            text-align: center;
        }}
        .zone-rank.top3 {{ color: var(--accent2); }}
        .zone-name {{
            color: var(--text);
            font-weight: 500;
            font-size: 0.87rem;
            line-height: 1.25;
        }}
        .zone-count {{
            font-family: 'JetBrains Mono', monospace;
            color: var(--accent1);
            font-weight: 600;
            font-size: 0.92rem;
        }}

        /* ---- Legend ---- */
        .legend-wrap {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }}
        .legend-bar {{
            flex: 1;
            height: 8px;
            border-radius: 4px;
            background: {t["legend_gradient"]};
            border: 1px solid var(--panel-border);
        }}
        .legend-label {{
            color: var(--text-dim);
            font-size: 0.72rem;
            letter-spacing: 0.02em;
            white-space: nowrap;
        }}

        /* ---- Data journalism narrative ---- */
        .dj-beat {{ padding: 3rem 0 1rem 0; max-width: 800px; }}
        .dj-kicker {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--accent2);
            margin-bottom: 14px;
        }}
        .dj-headline {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.15;
            letter-spacing: -0.025em;
            color: var(--text);
            margin: 0 0 14px 0;
        }}
        .dj-deck {{
            font-size: 1.02rem;
            line-height: 1.6;
            color: var(--text-muted);
            margin: 0 0 24px 0;
        }}
        .dj-divider {{
            border: 0;
            border-top: 1px solid var(--panel-border);
            margin: 4rem 0 0 0;
        }}

        /* ---- Source footer ---- */
        .source-footer {{
            margin-top: 5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--panel-border);
        }}
        .source-footer .source-label {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: var(--text-dim);
            margin-bottom: 6px;
        }}
        .source-footer .source-value {{ color: var(--text-muted); font-size: 0.9rem; }}
        .source-footer a {{
            color: var(--accent1);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color .2s ease;
        }}
        .source-footer a:hover {{ border-bottom-color: var(--accent1); }}

        .stPlotlyChart {{ background: transparent !important; }}
        .stPlotlyChart > div {{ background: transparent !important; }}

        iframe {{ border-radius: 14px; }}
        .element-container {{ margin-bottom: 0.6rem; }}
        </style>
        """, unsafe_allow_html=True)

    # ============================================================
    # Rendering
    # ============================================================
    def _render_masthead(self) -> None:
        top_l, top_r = st.columns([6, 1], vertical_alignment="center")
        with top_l:
            st.markdown('<h1 class="hero-title">TRAFIQ</h1>', unsafe_allow_html=True)
        with top_r:
            st.toggle("Light mode", key="light_mode")

        st.markdown(
            '<p class="hero-sub">Spatial intelligence on Qatar\'s road accidents, '
            'zone by zone and year by year.</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p class="source-line">Source: '
            f'<a href="{SOURCE_URL}" target="_blank" rel="noopener">{SOURCE_LABEL}</a></p>',
            unsafe_allow_html=True,
        )

    def _render_metrics(self) -> None:
        m = self.calculate_metrics()
        cards = [
            ("Annual Avg. Accidents", self.format_number(m["annual_avg"]), "1", "2020+"),
            ("Total Deaths",          f'{m["total_deaths"]:,}',            "3", "all years"),
            ("Pedestrian Deaths",     f'{m["pedestrian_deaths"]:,}',       "2", "collisions"),
            ("Total Accidents",       self.format_number(m["total_accidents"]), "1", "recorded"),
        ]
        cols = st.columns(4, gap="small")
        for col, (label, value, accent, sub) in zip(cols, cards):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value metric-accent-{accent}">{value}</div>
                    <div class="metric-sub">{sub}</div>
                </div>
                """, unsafe_allow_html=True)

    def _render_zone_list(self, year: int) -> None:
        year_data = self.df[self.df["ACCIDENT_YEAR"] == year]
        top = year_data["ZONE"].value_counts().head(8)
        for rank, (zone, count) in enumerate(top.items(), start=1):
            name = self.zone_names.get(str(zone), f"Zone {zone}")
            rank_class = "zone-rank top3" if rank <= 3 else "zone-rank"
            st.markdown(f"""
            <div class="zone-card">
                <div class="{rank_class}">#{rank}</div>
                <div class="zone-name">{name}</div>
                <div class="zone-count">{count:,}</div>
            </div>
            """, unsafe_allow_html=True)

    def _render_map_section(self, theme: dict) -> None:
        years = sorted(self.df["ACCIDENT_YEAR"].unique().tolist())

        title_col, _, year_col = st.columns([6, 2, 2], vertical_alignment="center")
        with title_col:
            st.markdown('<div class="section-title">Geographic Distribution</div>',
                        unsafe_allow_html=True)
        with year_col:
            year = st.selectbox(
                "Year", years, index=len(years) - 1,
                label_visibility="collapsed", key="year_select",
            )

        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

        map_col, side_col = st.columns([2.2, 1], gap="medium")

        with map_col:
            deck = self.create_map(year, theme)
            st.pydeck_chart(deck, width="stretch")
            st.markdown("""
            <div class="legend-wrap">
                <span class="legend-label">Low</span>
                <div class="legend-bar"></div>
                <span class="legend-label">High</span>
            </div>
            """, unsafe_allow_html=True)

        with side_col:
            st.markdown(f"""
            <div class="section-title" style="font-size:1rem;">
                Top Zones · {year}
            </div>
            <div style="height: 10px;"></div>
            """, unsafe_allow_html=True)
            self._render_zone_list(year)

    # ------------------------------------------------------------
    # Plotly helpers
    # ------------------------------------------------------------
    def _apply_plotly_theme(self, fig, theme: dict, showlegend: bool = False) -> None:
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Space Grotesk, sans-serif",
                color=theme["text"],
                size=12,
            ),
            title=dict(font=dict(color=theme["text"], size=14)),
            legend=dict(
                font=dict(color=theme["text"], size=11),
                bgcolor="rgba(0,0,0,0)",
                bordercolor=theme["panel_border"],
                borderwidth=0,
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
            ),
            xaxis=dict(
                title=dict(font=dict(color=theme["text"], size=12)),
                tickfont=dict(color=theme["text_muted"], size=11),
                gridcolor=theme["chart_grid"],
                zeroline=False,
                linecolor=theme["panel_border"],
            ),
            yaxis=dict(
                title=dict(font=dict(color=theme["text"], size=12)),
                tickfont=dict(color=theme["text_muted"], size=11),
                gridcolor=theme["chart_grid"],
                zeroline=False,
                linecolor=theme["panel_border"],
            ),
            showlegend=showlegend,
            margin=dict(l=10, r=10, t=20, b=10),
        )

    # ------------------------------------------------------------
    # Story beats
    # ------------------------------------------------------------
    def _story_header(self, kicker: str, headline: str, deck: str) -> None:
        st.markdown(f"""
        <div class="dj-beat">
            <div class="dj-kicker">{kicker}</div>
            <h2 class="dj-headline">{headline}</h2>
            <p class="dj-deck">{deck}</p>
        </div>
        """, unsafe_allow_html=True)

    def _story_severity(self, theme: dict) -> None:
        severity_col = "SEVERITY_EN" if "SEVERITY_EN" in self.df.columns else "ACCIDENT_SEVERITY"
        nature_col = "NATURE_EN" if "NATURE_EN" in self.df.columns else None
        if severity_col not in self.df.columns or not nature_col:
            return

        self._story_header(
            "01 · Severity",
            "What kinds of accidents get recorded?",
            "Nearly all incidents fall into a small number of collision types. "
            "Vehicle-to-vehicle collisions dominate the record, with pedestrian "
            "collisions forming a small but high-fatality slice.",
        )

        # Top 5 natures
        top_natures = (
            self.df[nature_col]
            .value_counts()
            .head(5)
            .index
            .tolist()
        )
        d = self.df[self.df[nature_col].isin(top_natures)].copy()

        # Build the cross-tab safely — crosstab then reindex (no .loc KeyError)
        counts = pd.crosstab(d[nature_col], d[severity_col])
        counts = counts.reindex(top_natures, fill_value=0)

        fig = px.bar(
            counts,
            barmode="stack",
            color_discrete_sequence=theme["chart_palette"],
        )
        fig.update_layout(barmode="stack")
        fig.update_yaxes(title_text="Accidents",
                         tickfont=dict(color=theme["text_muted"]))
        fig.update_xaxes(title_text="", tickangle=0)

        self._apply_plotly_theme(fig, theme, showlegend=True)
        fig.update_layout(height=420, bargap=0.35)
        st.plotly_chart(fig, width="stretch")

    def _story_age(self, theme: dict) -> None:
        birth_col = next(
            (c for c in ["BIRTH_YEAR_OF_ACCIDENT", "BIRTH_YEAR_OF_ACCIDENT_PERPETR"]
             if c in self.df.columns),
            None,
        )
        if not birth_col:
            return

        d = self.df.copy()
        d["AGE"] = d["ACCIDENT_YEAR"] - pd.to_numeric(d[birth_col], errors="coerce")
        d = d[(d["AGE"] >= 15) & (d["AGE"] <= 90)]
        if d.empty:
            return

        mean_age = d["AGE"].mean()

        self._story_header(
            "02 · Drivers",
            "Who is behind the wheel when accidents happen?",
            f"Filtered to drivers between 15 and 90, the distribution peaks in "
            f"the late 30s. Mean age across all recorded accidents is "
            f"{mean_age:.1f} years.",
        )

        age_counts = d.groupby("AGE").size().reset_index(name="count")

        fig = px.scatter(
            age_counts,
            x="AGE", y="count",
            color_discrete_sequence=[theme["accent1"]],
        )
        fig.update_traces(marker=dict(size=9, line=dict(width=0)))
        fig.update_xaxes(title_text="Driver age (years)")
        fig.update_yaxes(title_text="Accidents")

        self._apply_plotly_theme(fig, theme, showlegend=False)
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")

    def _story_hour(self, theme: dict) -> None:
        if "HOUR" not in self.df.columns:
            return
        hour_counts = (
            self.df.dropna(subset=["HOUR"])
            .groupby("HOUR").size().reset_index(name="count")
        )
        if hour_counts.empty:
            return

        peak_hour = int(hour_counts.loc[hour_counts["count"].idxmax(), "HOUR"])
        peak_label = f"{peak_hour:02d}:00"

        self._story_header(
            "03 · Time",
            "When do accidents happen most?",
            f"The hourly pattern is unmistakable. The daily peak lands around "
            f"{peak_label}, aligning with evening rush. Early morning hours "
            f"remain the safest window.",
        )

        fig = px.bar(
            hour_counts, x="HOUR", y="count",
            color_discrete_sequence=[theme["accent2"]],
        )
        fig.update_xaxes(
            title_text="Hour of day",
            tickmode="array",
            tickvals=list(range(0, 24, 2)),
            ticktext=[f"{h:02d}h" for h in range(0, 24, 2)],
        )
        fig.update_yaxes(title_text="Accidents")

        self._apply_plotly_theme(fig, theme, showlegend=False)
        fig.update_layout(height=400, bargap=0.15)
        st.plotly_chart(fig, width="stretch")

    def _render_story(self, theme: dict) -> None:
        st.markdown('<hr class="dj-divider"/>', unsafe_allow_html=True)
        self._story_severity(theme)
        self._story_age(theme)
        self._story_hour(theme)

    def _render_footer(self) -> None:
        st.markdown(f"""
        <footer class="source-footer">
            <div class="source-label">Source</div>
            <div class="source-value">
                <a href="{SOURCE_URL}" target="_blank" rel="noopener">
                    {SOURCE_LABEL}
                </a>
            </div>
        </footer>
        """, unsafe_allow_html=True)

    # ============================================================
    # Main
    # ============================================================
    def run_dashboard(self) -> None:
        st.set_page_config(page_title="TRAFIQ", layout="wide")

        if "light_mode" not in st.session_state:
            st.session_state.light_mode = False

        theme = LIGHT if st.session_state.light_mode else DARK

        self._inject_css(theme)
        self._render_masthead()

        if self.load_error or self.df is None or self.df.empty:
            st.error("Accident data could not be loaded.")
            if self.load_error:
                st.markdown(f"**Reason:** {self.load_error}")
            return

        self._render_metrics()
        st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)

        if self.zones_data:
            self._render_map_section(theme)

        self._render_story(theme)
        self._render_footer()


if __name__ == "__main__":
    QatarAccidentsStreamlit().run_dashboard()