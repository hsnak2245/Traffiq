import streamlit as st
import pandas as pd
import numpy as np
import json
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


# ============================================================
# Map style: Esri Dark Gray Canvas (free, no API key)
# ============================================================
ESRI_DARK_STYLE = {
    "version": 8,
    "sources": {
        "esri-dark": {
            "type": "raster",
            "tiles": [
                "https://server.arcgisonline.com/ArcGIS/rest/services/"
                "Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
            ],
            "tileSize": 256,
            "attribution": "Esri, HERE, Garmin, © OpenStreetMap contributors",
        }
    },
    "layers": [{"id": "esri-dark", "type": "raster", "source": "esri-dark"}],
}


class QatarAccidentsStreamlit:

    def __init__(self,
                 accidents_file: str = "facc.csv",
                 polygons_file: str = "qatar_zones_polygons.json"):
        self.accidents_file = accidents_file
        self.polygons_file = polygons_file
        self.df: pd.DataFrame | None = None
        self.zones_data: dict | None = None
        self.zone_names: dict = self._load_zone_names()

        # Neon palette
        self.colors = {
            "bg": "#0a0a0a",
            "panel": "rgba(255,255,255,0.03)",
            "text": "#f0f0f0",
            "muted": "#7a7a7a",
            "pink": "#FF00FF",
            "cyan": "#00FFFF",
            "red": "#FF3333",
        }

        self.load_data()

    # ------------------------------------------------------------
    # Zone names
    # ------------------------------------------------------------
    def _load_zone_names(self) -> dict:
        try:
            with open("zone_names.json") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Could not load zone names: {e}")
            return {}

    # ------------------------------------------------------------
    # Data loading + cleaning (Arrow-safe)
    # ------------------------------------------------------------
    def load_data(self) -> None:
        if not Path(self.accidents_file).is_file():
            st.error(f"Accidents file '{self.accidents_file}' not found.")
            return

        self.df = pd.read_csv(self.accidents_file, skipinitialspace=True)

        # --- Clean ZONE (vectorized, Arrow-safe) ---
        zone_numeric = pd.to_numeric(
            self.df["ZONE"].astype(str).str.strip(), errors="coerce"
        )
        self.df["ZONE"] = np.where(
            zone_numeric.notna(),
            zone_numeric.fillna(0).astype(int).astype(str),
            "Unknown",
        )

        # --- Clean YEAR (fixes 2024.0 display) ---
        self.df["ACCIDENT_YEAR"] = pd.to_numeric(
            self.df["ACCIDENT_YEAR"], errors="coerce"
        )
        self.df = self.df.dropna(subset=["ACCIDENT_YEAR"])
        self.df["ACCIDENT_YEAR"] = self.df["ACCIDENT_YEAR"].astype(int)

        # --- Extract hour ---
        self.df["HOUR"] = (
            self.df["ACCIDENT_TIME"]
            .astype(str)
            .str.extract(r"(\d+)", expand=False)
            .astype(float)
        )

        # --- Numeric death count ---
        self.df["DEATH_COUNT"] = pd.to_numeric(
            self.df["DEATH_COUNT"], errors="coerce"
        ).fillna(0).astype(int)

        # --- Load polygons ---
        if not Path(self.polygons_file).is_file():
            st.warning(f"Polygon file '{self.polygons_file}' not found.")
            return
        try:
            with open(self.polygons_file) as f:
                self.zones_data = json.load(f)
        except Exception as e:
            st.warning(f"Could not load polygons: {e}")

    # ------------------------------------------------------------
    # Color interpolation: magenta -> cyan -> red
    # ------------------------------------------------------------
    @staticmethod
    def _interpolate_color(t: float, alpha: int = 190) -> list[int]:
        """t in [0, 1] -> [r, g, b, alpha]."""
        t = max(0.0, min(1.0, t))
        if t <= 0.5:
            u = t / 0.5
            r, g, b = int(255 * (1 - u)), int(255 * u), 255
        else:
            u = (t - 0.5) / 0.5
            r, g, b = 255, int(255 * (1 - u)), int(255 * (1 - u))
        return [r, g, b, alpha]

    # ------------------------------------------------------------
    # Build GeoJSON for a given year (with per-feature color)
    # ------------------------------------------------------------
    def build_geojson(self, year: int) -> dict:
        if self.df is None or self.zones_data is None:
            return {"type": "FeatureCollection", "features": []}

        year_data = self.df[self.df["ACCIDENT_YEAR"] == year]
        zone_counts = year_data["ZONE"].value_counts().to_dict()
        max_count = max(zone_counts.values()) if zone_counts else 1

        features = []
        for zone_id, z in self.zones_data.items():
            count = int(zone_counts.get(zone_id, 0))
            t = count / max_count if max_count else 0
            coords = [[p["lng"], p["lat"]] for p in z["coordinates"]]
            features.append({
                "type": "Feature",
                "properties": {
                    "zone_id": zone_id,
                    "name": self.zone_names.get(zone_id, f"Zone {zone_id}"),
                    "count": count,
                    "color": self._interpolate_color(t),
                },
                "geometry": {"type": "Polygon", "coordinates": [coords]},
            })
        return {"type": "FeatureCollection", "features": features}

    # ------------------------------------------------------------
    # PyDeck map
    # ------------------------------------------------------------
    def create_map(self, year: int) -> pdk.Deck:
        geojson = self.build_geojson(year)

        layer = pdk.Layer(
            "GeoJsonLayer",
            data=geojson,
            get_fill_color="properties.color",
            get_line_color=[30, 30, 30, 200],
            get_line_width=1,
            line_width_min_pixels=1,
            pickable=True,
            auto_highlight=True,
            filled=True,
            stroked=True,
        )

        view_state = pdk.ViewState(
            latitude=25.2867,
            longitude=51.5333,
            zoom=10.5,
            pitch=0,
            bearing=0,
        )

        return pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style=ESRI_DARK_STYLE,
            tooltip={
                "html": "<b>{name}</b><br/>Accidents: <b>{count}</b>",
                "style": {
                    "backgroundColor": "#111",
                    "color": "#00FFFF",
                    "fontFamily": "Inter, sans-serif",
                    "borderRadius": "8px",
                    "padding": "8px 12px",
                },
            },
        )

    # ------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------
    def calculate_metrics(self) -> dict:
        if self.df is None or self.df.empty:
            return {"annual_avg": 0, "total_deaths": 0,
                    "pedestrian_deaths": 0, "total_accidents": 0}

        recent = self.df[self.df["ACCIDENT_YEAR"] >= 2020]
        n_years = recent["ACCIDENT_YEAR"].nunique()
        annual_avg = len(recent) / n_years if n_years else 0

        total_deaths = int(self.df["DEATH_COUNT"].sum())

        ped_deaths = int(
            self.df[
                self.df["ACCIDENT_NATURE"].astype(str).str.upper()
                == "COLLISION WITH PEDESTRIANS"
            ]["DEATH_COUNT"].sum()
        )

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
    # UI SECTIONS
    # ============================================================
    def _inject_css(self) -> None:
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        .stApp {
            background:
                radial-gradient(circle at 15% 10%, rgba(255,0,255,0.08), transparent 45%),
                radial-gradient(circle at 85% 5%, rgba(0,255,255,0.07), transparent 45%),
                #0a0a0a;
            color: #f0f0f0;
        }

        #MainMenu, footer, header { visibility: hidden; }

        .block-container { padding-top: 1rem; padding-bottom: 3rem; max-width: 1400px; }

        /* Hero */
        .hero-title {
            font-size: 3.2rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            background: linear-gradient(90deg, #00FFFF 0%, #FF00FF 60%, #FF3355 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            line-height: 1.1;
        }
        .hero-sub {
            color: #8a8a8a;
            font-size: 1.05rem;
            margin-top: 0.4rem;
            margin-bottom: 2rem;
            font-weight: 400;
        }

        /* Home button */
        .home-button {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #b0b0b0;
            text-decoration: none;
            font-weight: 500;
            padding: 6px 12px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.08);
            transition: all .2s ease;
            margin-bottom: 1rem;
        }
        .home-button:hover { color: #00FFFF; border-color: rgba(0,255,255,0.4); }

        /* Metric card */
        .metric-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 22px 24px;
            height: 100%;
            position: relative;
            overflow: hidden;
            transition: all .25s ease;
        }
        .metric-card:hover {
            border-color: rgba(0,255,255,0.3);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,255,255,0.08);
        }
        .metric-label {
            color: #8a8a8a;
            font-size: 0.82rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        }
        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.2rem;
            font-weight: 700;
            color: #ffffff;
            line-height: 1;
        }
        .metric-accent-cyan  { color: #00FFFF; }
        .metric-accent-pink  { color: #FF66FF; }
        .metric-accent-red   { color: #FF4466; }

        /* Section title */
        .section-title {
            font-size: 1.35rem;
            font-weight: 700;
            color: #ffffff;
            margin: 2.2rem 0 1rem 0;
            letter-spacing: -0.01em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-title::before {
            content: '';
            width: 4px;
            height: 22px;
            background: linear-gradient(180deg, #00FFFF, #FF00FF);
            border-radius: 2px;
        }

        /* Zone card */
        .zone-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            margin-bottom: 8px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-left: 3px solid #00FFFF;
            border-radius: 10px;
            transition: all .2s ease;
        }
        .zone-card:hover {
            background: rgba(0,255,255,0.06);
            border-left-color: #FF00FF;
            transform: translateX(3px);
        }
        .zone-name  { color: #e0e0e0; font-weight: 500; font-size: 0.92rem; }
        .zone-count {
            font-family: 'JetBrains Mono', monospace;
            color: #00FFFF;
            font-weight: 600;
            font-size: 0.95rem;
        }

        /* Legend */
        .legend-bar {
            height: 10px;
            border-radius: 5px;
            background: linear-gradient(90deg, #FF00FF 0%, #00FFFF 50%, #FF0000 100%);
            margin: 6px 0 4px 0;
        }
        .legend-labels {
            display: flex;
            justify-content: space-between;
            color: #7a7a7a;
            font-size: 0.75rem;
        }

        /* Selectbox tweak */
        div[data-baseweb="select"] > div {
            background-color: rgba(255,255,255,0.04) !important;
            border-color: rgba(255,255,255,0.1) !important;
            border-radius: 10px !important;
        }
        div[data-baseweb="select"] > div:hover {
            border-color: rgba(0,255,255,0.5) !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: transparent;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: #8a8a8a;
            border-radius: 8px 8px 0 0;
            padding: 8px 18px;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            color: #00FFFF !important;
            border-bottom: 2px solid #00FFFF;
        }

        /* PyDeck iframe rounding */
        iframe { border-radius: 16px; }
        </style>
        """, unsafe_allow_html=True)

    def _render_hero(self) -> None:
        st.markdown("""
        <a href="https://traffiq.streamlit.app/" class="home-button">
            <span>🏠</span><span>Home</span>
        </a>
        """, unsafe_allow_html=True)

        st.markdown('<h1 class="hero-title">TraffiiQ</h1>', unsafe_allow_html=True)
        st.markdown(
            '<p class="hero-sub">Spatial intelligence on Qatar\'s road accidents — '
            'zone by zone, year by year.</p>',
            unsafe_allow_html=True,
        )

    def _render_metrics(self) -> None:
        m = self.calculate_metrics()

        cards = [
            ("Annual Avg. Accidents", self.format_number(m["annual_avg"]), "cyan", "2020+"),
            ("Total Deaths",          f'{m["total_deaths"]:,}',            "red",  "all years"),
            ("Pedestrian Deaths",     f'{m["pedestrian_deaths"]:,}',       "pink", "collisions"),
            ("Total Accidents",       self.format_number(m["total_accidents"]), "cyan", "recorded"),
        ]

        cols = st.columns(4)
        for col, (label, value, accent, sub) in zip(cols, cards):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value metric-accent-{accent}">{value}</div>
                    <div style="color:#5a5a5a;font-size:0.75rem;margin-top:8px;
                                text-transform:uppercase;letter-spacing:0.06em;">
                        {sub}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    def _render_zone_sidebar(self, year: int) -> None:
        year_data = self.df[self.df["ACCIDENT_YEAR"] == year]
        top = year_data["ZONE"].value_counts().head(8)

        for zone, count in top.items():
            name = self.zone_names.get(str(zone), f"Zone {zone}")
            st.markdown(f"""
            <div class="zone-card">
                <span class="zone-name">{name}</span>
                <span class="zone-count">{count:,}</span>
            </div>
            """, unsafe_allow_html=True)

    def _render_map_section(self) -> None:
        years = sorted(self.df["ACCIDENT_YEAR"].unique().tolist())

        ctrl_l, ctrl_r = st.columns([3, 1])
        with ctrl_l:
            st.markdown('<div class="section-title">Geographic Distribution</div>',
                        unsafe_allow_html=True)
        with ctrl_r:
            year = st.selectbox(
                "Year",
                years,
                index=len(years) - 1,
                label_visibility="collapsed",
            )

        map_col, side_col = st.columns([2.2, 1])

        with map_col:
            deck = self.create_map(year)
            st.pydeck_chart(deck, use_container_width=True, height=560)

            # Legend
            st.markdown("""
            <div class="legend-bar"></div>
            <div class="legend-labels">
                <span>Low accidents</span>
                <span>Medium</span>
                <span>High</span>
            </div>
            """, unsafe_allow_html=True)

        with side_col:
            st.markdown(f"""
            <div class="section-title" style="font-size:1.05rem;margin-top:0;">
                Top Zones · {year}
            </div>
            """, unsafe_allow_html=True)
            self._render_zone_sidebar(year)

    def _render_insights(self) -> None:
        st.markdown('<div class="section-title">Insights</div>', unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📊 Severity", "👥 Age", "🕐 Hour"])

        chart_layout = dict(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0e0",
            margin=dict(l=10, r=10, t=40, b=10),
        )

        with tab1:
            category = st.selectbox(
                "Break down by:",
                ["NATIONALITY_GROUP_OF_ACCIDENT", "ACCIDENT_NATURE",
                 "ACCIDENT_REASON", "ACCIDENT_SEVERITY"],
                format_func=lambda x: x.replace("_", " ").title(),
                key="cat_select",
            )
            if category in self.df.columns:
                counts = (self.df.groupby([category, "ACCIDENT_SEVERITY"])
                                .size().unstack(fill_value=0))
                fig = px.bar(
                    counts, barmode="stack",
                    title=f"Severity by {category.replace('_', ' ').title()}",
                    color_discrete_sequence=px.colors.sequential.Plasma,
                )
                fig.update_layout(**chart_layout)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Column '{category}' not found in dataset.")

        with tab2:
            birth_col = "BIRTH_YEAR_OF_ACCIDENT"
            if birth_col in self.df.columns:
                d = self.df.copy()
                d["AGE"] = d["ACCIDENT_YEAR"] - pd.to_numeric(
                    d[birth_col], errors="coerce"
                )
                d = d[(d["AGE"] >= 0) & (d["AGE"] <= 90)]
                age_counts = d.groupby("AGE").size().reset_index(name="count")
                mean_age = d["AGE"].mean()
                fig = px.scatter(
                    age_counts, x="AGE", y="count", size="count",
                    title="Accidents by Driver Age",
                    color_discrete_sequence=["#FF00FF"],
                )
                fig.add_annotation(
                    x=0.98, y=1.06, xref="paper", yref="paper",
                    text=f"Mean age: {mean_age:.1f}",
                    showarrow=False, font=dict(color="#00FFFF", size=12),
                )
                fig.update_layout(**chart_layout)
                st.plotly_chart(fig, use_container_width=True)

        with tab3:
            hour_counts = (self.df.dropna(subset=["HOUR"])
                               .groupby("HOUR").size().reset_index(name="count"))
            fig = px.bar(
                hour_counts, x="HOUR", y="count",
                title="Accidents by Hour of Day",
                color_discrete_sequence=["#00FFFF"],
            )
            fig.update_layout(**chart_layout)
            st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------
    def run_dashboard(self) -> None:
        st.set_page_config(
            page_title="TraffiiQ · Accident Analytics",
            page_icon="🚗",
            layout="wide",
        )
        self._inject_css()
        self._render_hero()

        if self.df is None or self.df.empty:
            st.error("No accident data loaded. Check `facc.csv`.")
            return

        self._render_metrics()
        self._render_map_section()
        self._render_insights()


if __name__ == "__main__":
    QatarAccidentsStreamlit().run_dashboard()