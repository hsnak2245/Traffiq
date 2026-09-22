import streamlit as st
import pandas as pd
import numpy as np
import json
import pydeck as pdk
import plotly.express as px
from pathlib import Path


# ============================================================
# Map style — Carto Dark Matter GL style (string URL, no API key)
# ============================================================
DARK_MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"


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

    # ------------------------------------------------------------
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
            self.load_error = f"`{self.accidents_file}` is empty (0 bytes)."
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
    # Color scale: cool cyan (low) → magenta (mid) → hot red (high)
    # Zero-count zones stay nearly invisible
    # ------------------------------------------------------------
    @staticmethod
    def _interpolate_color(t: float) -> list:
        """t in [0,1]: 0 = cool cyan, 0.5 = magenta, 1 = hot red."""
        t = max(0.0, min(1.0, t))
        if t <= 0.5:
            u = t / 0.5
            r = int(0 + u * 255)
            g = int(220 * (1 - u))
            b = int(255 - u * 0)
            a = int(120 + u * 100)
        else:
            u = (t - 0.5) / 0.5
            r = int(255)
            g = int(0 + u * 60)
            b = int(255 * (1 - u))
            a = int(220 - u * 20)
        return [r, g, b, a]

    # ------------------------------------------------------------
    def build_geojson(self, year: int) -> dict:
        if self.df is None or self.zones_data is None:
            return {"type": "FeatureCollection", "features": []}

        year_data = self.df[self.df["ACCIDENT_YEAR"] == year]
        zone_counts = year_data["ZONE"].value_counts().to_dict()

        # Rank-based normalization for smoother distribution
        counts = sorted(zone_counts.values(), reverse=True)
        max_count = counts[0] if counts else 1

        features = []
        for zone_id, z in self.zones_data.items():
            count = int(zone_counts.get(zone_id, 0))
            if count == 0:
                color = [40, 40, 40, 30]
            else:
                # Use log-ish scale so mid-range zones stay visible
                t = (count / max_count) ** 0.7
                color = self._interpolate_color(t)

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
    def create_map(self, year: int) -> pdk.Deck:
        geojson = self.build_geojson(year)

        layer = pdk.Layer(
            "GeoJsonLayer",
            data=geojson,
            get_fill_color="properties.color",
            get_line_color=[90, 90, 90, 180],
            get_line_width=1.2,
            line_width_min_pixels=1,
            pickable=True,
            auto_highlight=True,
            highlight_color=[0, 255, 255, 100],
            filled=True,
            stroked=True,
        )

        view_state = pdk.ViewState(
            latitude=25.2867,
            longitude=51.5333,
            zoom=10.6,
            pitch=0,
            bearing=0,
        )

        return pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style=DARK_MAP_STYLE,
            tooltip={
                "html": "<b>{name}</b><br/>Accidents: <b>{count}</b>",
                "style": {
                    "backgroundColor": "#0f0f0f",
                    "color": "#00FFFF",
                    "fontFamily": "Space Grotesk, sans-serif",
                    "borderRadius": "8px",
                    "padding": "8px 12px",
                    "border": "1px solid rgba(0,255,255,0.3)",
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
    # UI
    # ============================================================
    def _inject_css(self) -> None:
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

        html, body, [class*="css"], .stApp, .stMarkdown, .stMetric,
        button, input, select, textarea {
            font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        .stApp {
            background:
                radial-gradient(circle at 15% 10%, rgba(255,0,255,0.08), transparent 45%),
                radial-gradient(circle at 85% 5%, rgba(0,255,255,0.07), transparent 45%),
                #0a0a0a;
            color: #f0f0f0;
        }

        #MainMenu, footer, header { visibility: hidden; }
        .block-container { padding-top: 1rem; padding-bottom: 3rem; max-width: 1400px; }

        .hero-title {
            font-size: 3.2rem; font-weight: 700;
            letter-spacing: -0.035em;
            background: linear-gradient(90deg, #00FFFF 0%, #FF00FF 60%, #FF3355 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0; line-height: 1.05;
        }
        .hero-sub {
            color: #8a8a8a; font-size: 1.05rem;
            margin-top: 0.4rem; margin-bottom: 2rem; font-weight: 400;
        }
        .home-button {
            display: inline-flex; align-items: center; gap: 6px;
            color: #b0b0b0; text-decoration: none; font-weight: 500;
            padding: 6px 12px; border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.08);
            transition: all .2s ease; margin-bottom: 1rem;
        }
        .home-button:hover { color: #00FFFF; border-color: rgba(0,255,255,0.4); }

        /* ---- Metric cards ---- */
        .metric-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.045) 0%, rgba(255,255,255,0.012) 100%);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 14px;
            padding: 18px 22px;
            height: 100%;
            transition: all .25s ease;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .metric-card:hover {
            border-color: rgba(0,255,255,0.28);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,255,255,0.06);
        }
        .metric-label {
            color: #8a8a8a; font-size: 0.72rem; font-weight: 500;
            text-transform: uppercase; letter-spacing: 0.1em;
            margin-bottom: 10px;
        }
        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.05rem; font-weight: 600;
            color: #ffffff; line-height: 1;
        }
        .metric-accent-cyan { color: #00FFFF; }
        .metric-accent-pink { color: #FF66FF; }
        .metric-accent-red  { color: #FF4466; }
        .metric-sub {
            color: #5a5a5a; font-size: 0.68rem;
            margin-top: 10px;
            text-transform: uppercase; letter-spacing: 0.09em;
        }

        /* ---- Section title ---- */
        .section-title {
            font-size: 1.3rem; font-weight: 600; color: #ffffff;
            margin: 0; letter-spacing: -0.015em;
            display: flex; align-items: center; gap: 10px;
        }
        .section-title::before {
            content: ''; width: 4px; height: 20px;
            background: linear-gradient(180deg, #00FFFF, #FF00FF);
            border-radius: 2px;
        }

        /* ---- Year selector: make it compact & aligned ---- */
        div[data-baseweb="select"] > div {
            background-color: rgba(255,255,255,0.05) !important;
            border-color: rgba(0,255,255,0.25) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace !important;
        }
        div[data-baseweb="select"] > div:hover {
            border-color: rgba(0,255,255,0.6) !important;
        }

        /* ---- Zone cards with rank badge ---- */
        .zone-card {
            display: grid;
            grid-template-columns: 26px 1fr auto;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            margin-bottom: 8px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 10px;
            transition: all .2s ease;
        }
        .zone-card:hover {
            background: rgba(0,255,255,0.06);
            border-color: rgba(0,255,255,0.25);
            transform: translateX(3px);
        }
        .zone-rank {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            font-weight: 600;
            color: #6a6a6a;
            text-align: center;
        }
        .zone-rank.top3 {
            color: #FF00FF;
        }
        .zone-name {
            color: #e0e0e0;
            font-weight: 500;
            font-size: 0.87rem;
            line-height: 1.25;
        }
        .zone-count {
            font-family: 'JetBrains Mono', monospace;
            color: #00FFFF;
            font-weight: 600;
            font-size: 0.92rem;
        }

        /* ---- Legend ---- */
        .legend-wrap {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }
        .legend-bar {
            flex: 1;
            height: 8px;
            border-radius: 4px;
            background: linear-gradient(90deg, #00dcdc 0%, #ff00ff 50%, #ff2222 100%);
        }
        .legend-label {
            color: #7a7a7a;
            font-size: 0.72rem;
            letter-spacing: 0.02em;
            white-space: nowrap;
        }

        /* ---- Tabs ---- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px; background: transparent;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent; color: #8a8a8a;
            border-radius: 8px 8px 0 0; padding: 8px 18px;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            color: #00FFFF !important;
            border-bottom: 2px solid #00FFFF;
        }

        iframe { border-radius: 14px; }

        /* Reduce vertical gap between stacked elements */
        .element-container { margin-bottom: 0.6rem; }
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

    def _render_zone_sidebar(self, year: int) -> None:
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

    def _render_map_section(self) -> None:
        years = sorted(self.df["ACCIDENT_YEAR"].unique().tolist())

        # ---- Title and year selector on the SAME row, baseline-aligned ----
        title_col, spacer, year_col = st.columns([6, 2, 2], vertical_alignment="center")
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
            deck = self.create_map(year)
            st.pydeck_chart(deck, use_container_width=True)

            # Legend pinned beneath the map
            st.markdown("""
            <div class="legend-wrap">
                <span class="legend-label">Low</span>
                <div class="legend-bar"></div>
                <span class="legend-label">High</span>
            </div>
            """, unsafe_allow_html=True)

        with side_col:
            st.markdown(f"""
            <div class="section-title" style="font-size:1.05rem;">
                Top Zones · {year}
            </div>
            <div style="height: 10px;"></div>
            """, unsafe_allow_html=True)
            self._render_zone_sidebar(year)

    def _render_insights(self) -> None:
        st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Insights</div>', unsafe_allow_html=True)
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📊 Severity", "👥 Age", "🕐 Hour"])

        chart_layout = dict(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0e0",
            font_family="Space Grotesk, sans-serif",
            margin=dict(l=10, r=10, t=40, b=10),
        )

        with tab1:
            candidates = [
                "NATIONALITY_GROUP_OF_ACCIDENT",
                "NATURE_EN",
                "ACCIDENT_NATURE",
                "ACCIDENT_REASON",
            ]
            available = [c for c in candidates if c in self.df.columns]
            severity_col = "SEVERITY_EN" if "SEVERITY_EN" in self.df.columns else "ACCIDENT_SEVERITY"

            if not available:
                st.info("No breakdown columns available in dataset.")
            else:
                category = st.selectbox(
                    "Break down by:", available,
                    format_func=lambda x: x.replace("_", " ").strip().title(),
                    key="cat_select",
                )
                if severity_col in self.df.columns:
                    counts = (
                        self.df.groupby([category, severity_col])
                        .size().unstack(fill_value=0)
                    )
                    fig = px.bar(
                        counts, barmode="stack",
                        title=f"Severity by {category.replace('_', ' ').title()}",
                        color_discrete_sequence=px.colors.sequential.Plasma,
                    )
                    fig.update_layout(**chart_layout)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Severity column missing.")

        with tab2:
            birth_col = next((c for c in
                              ["BIRTH_YEAR_OF_ACCIDENT", "BIRTH_YEAR_OF_ACCIDENT_PERPETR"]
                              if c in self.df.columns), None)
            if birth_col:
                d = self.df.copy()
                d["AGE"] = d["ACCIDENT_YEAR"] - pd.to_numeric(d[birth_col], errors="coerce")
                d = d[(d["AGE"] >= 0) & (d["AGE"] <= 90)]
                age_counts = d.groupby("AGE").size().reset_index(name="count")
                mean_age = d["AGE"].mean() if len(d) else float("nan")

                fig = px.scatter(
                    age_counts, x="AGE", y="count", size="count",
                    title="Accidents by Driver Age",
                    color_discrete_sequence=["#FF00FF"],
                )
                if pd.notna(mean_age):
                    fig.add_annotation(
                        x=0.98, y=1.06, xref="paper", yref="paper",
                        text=f"Mean age: {mean_age:.1f}",
                        showarrow=False,
                        font=dict(color="#00FFFF", size=12),
                    )
                fig.update_layout(**chart_layout)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Birth year column not available.")

        with tab3:
            if "HOUR" in self.df.columns:
                hour_counts = (
                    self.df.dropna(subset=["HOUR"])
                    .groupby("HOUR").size().reset_index(name="count")
                )
                fig = px.bar(
                    hour_counts, x="HOUR", y="count",
                    title="Accidents by Hour of Day",
                    color_discrete_sequence=["#00FFFF"],
                )
                fig.update_layout(**chart_layout)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Accident time column not available.")

    # ------------------------------------------------------------
    def run_dashboard(self) -> None:
        st.set_page_config(
            page_title="TraffiiQ · Accident Analytics",
            page_icon="🚗", layout="wide",
        )
        self._inject_css()
        self._render_hero()

        if self.load_error or self.df is None or self.df.empty:
            st.error("⚠️ Accident data could not be loaded.")
            if self.load_error:
                st.markdown(f"**Reason:** {self.load_error}")
            return

        self._render_metrics()
        st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)

        if self.zones_data:
            self._render_map_section()
        else:
            st.warning("Zone polygons not loaded — map section skipped.")

        self._render_insights()


if __name__ == "__main__":
    QatarAccidentsStreamlit().run_dashboard()