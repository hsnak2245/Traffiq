import streamlit as st
import pandas as pd
import json
from streamlit_folium import st_folium
import folium
import folium
from folium import plugins
import branca.colormap as cm
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar
from pathlib import Path
import branca.element as be

class QatarAccidentsStreamlit:
    def __init__(self, accidents_file='facc.csv', polygons_file='qatar_zones_polygons.json'):
        self.accidents_file = accidents_file
        self.polygons_file = polygons_file
        self.df = None
        self.zones_data = None
        self.zone_names = self.initialize_zone_names()
        self.current_year = None
        
        # Color scheme
        self.colors = {
            'background': '#111111',
            'text': '#FFFFFF',
            'neon_pink': '#FF00FF',
            'neon_cyan': '#00FFFF',
            'neon_green': '#39FF14',
            'maroon': '#800000'
        }
        
        # Load and process data
        self.load_data()
        
    def initialize_zone_names(self):
        try:
            with open('zone_names.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            st.warning("Zone names file not found. Please ensure 'zone_names.json' is available.")
            return {}
        except Exception as e:
            st.warning(f"Could not load zone names: {e}")
            return {}

    def load_data(self):
        # Check if accidents file exists
        if not Path(self.accidents_file).is_file():
            st.error(f"Accidents file '{self.accidents_file}' not found. Please ensure the file is available.")
            return
        
        # Load accidents data
        self.df = pd.read_csv(self.accidents_file, skipinitialspace=True)
        
        # Clean data
        self.df['ZONE'] = self.df['ZONE'].astype(str).str.strip()
        self.df['ZONE'] = self.df['ZONE'].apply(lambda x: 
            str(int(float(x))) if x.replace('.', '').isdigit() else 'Unknown')
        
        # Convert time to hour
        self.df['HOUR'] = self.df['ACCIDENT_TIME'].str.extract('(\d+)').astype(float)
        
        # Set current year to the most recent year
        self.current_year = self.df['ACCIDENT_YEAR'].max()
        
        # Check if polygons file exists
        if not Path(self.polygons_file).is_file():
            st.warning(f"Polygon file '{self.polygons_file}' not found. Please ensure the file is available.")
            return
        
        # Load polygon data
        try:
            with open(self.polygons_file, 'r') as f:
                self.zones_data = json.load(f)
        except Exception as e:
            st.warning(f"Could not load polygon data: {e}")

    def create_map(self, year):
        # Create base map
        m = folium.Map(
            location=[25.2867, 51.5333],
            zoom_start=11,
            tiles='CartoDB dark_matter',
            prefer_canvas=True
        )
        
        # Get accident counts for the selected year
        year_data = self.df[self.df['ACCIDENT_YEAR'] == year]
        zone_counts = year_data['ZONE'].value_counts().to_dict()
        max_count = max(zone_counts.values()) if zone_counts else 1
        
        # Create color scale
        colormap = cm.LinearColormap(
            colors=['#ff00ff', '#00ffff', '#ff0000'],
            vmin=0,
            vmax=max_count
        )
        
        # Add zones to map
        for zone, count in zone_counts.items():
            try:
                if zone.lower() == 'unknown':
                    continue
                    
                zone_int = str(int(float(zone)))
                zone_data = self.zones_data.get(zone_int)
                zone_name = self.zone_names.get(zone_int, f'Zone {zone_int}')
                
                if zone_data:
                    coordinates = [[p['lat'], p['lng']] for p in zone_data['coordinates']]
                    opacity = 0.2 + (count / max_count * 0.8)
                    
                    folium.Polygon(
                        locations=coordinates,
                        weight=0,
                        fill=True,
                        fill_color=colormap(count),
                        fill_opacity=opacity,
                        popup=f'{zone_name}<br>Accidents: {count}',
                        tooltip=zone_name
                    ).add_to(m)
                    
            except Exception as e:
                st.error(f"Error processing zone {zone}: {str(e)}")
                
        # Add the color scale
        colormap.add_to(m)
        
        return m

    def calculate_metrics(self):
        # Calculate annual average accidents from 2020 onwards
        recent_data = self.df[self.df['ACCIDENT_YEAR'] >= 2020]
        annual_avg = len(recent_data) / len(recent_data['ACCIDENT_YEAR'].unique())
        
        # Calculate total deaths till 2024
        total_deaths = self.df['DEATH_COUNT'].sum()
        
        # Calculate pedestrian collision deaths
        pedestrian_deaths = self.df[
            self.df['ACCIDENT_NATURE'] == 'COLLISION WITH PEDESTRIANS'
        ]['DEATH_COUNT'].sum()
        
        # Calculate total accidents
        total_accidents = len(self.df)
        
        return {
            'annual_avg': round(annual_avg, 1),
            'total_deaths': int(total_deaths),
            'pedestrian_deaths': int(pedestrian_deaths),
            'total_accidents': total_accidents
        }

    def format_number(self, num):
        if num >= 1_000_000:
            return f'{num/1_000_000:.1f}M+'
        elif num >= 1_000:
            return f'{num/1_000:.1f}K+'
        else:
            return str(num)

    def run_dashboard(self):
        # Set page config
        st.set_page_config(page_title="TraffiiQ", page_icon="🚗", layout="wide")

        # Custom CSS
        st.markdown("""
        <style>
        .stApp {
            background-color: #111111;
            color: #FFFFFF;
        }
        .stMetric {
            background-color: #222222;
            padding: 20px;
            border-radius: 10px;
        }
        .home-button {
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            display: flex;
            align-items: center;
        }
        .home-button:hover {
            color: #00FFFF;
        }
        .home-button-icon {
            margin-right: 5px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Home button
        st.markdown("""
        <a href="https://traffiq.streamlit.app/" class="home-button">
            <span class="home-button-icon">🏠</span>
            <span>Home</span>
        </a>
        """, unsafe_allow_html=True)

        # Title
        st.markdown("<h1 style='text-align: center; color: #00FFFF;'>TraffiiQ</h1>", unsafe_allow_html=True)
        
        # Calculate metrics
        metrics = self.calculate_metrics()
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Annual Avg. Accidents (2020+)", self.format_number(metrics['annual_avg']))
        with col2:
            st.metric("Total Deaths", self.format_number(metrics['total_deaths']))
        with col3:
            st.metric("Pedestrian Collision Deaths", self.format_number(metrics['pedestrian_deaths']))
        with col4:
            st.metric("Total Accidents", self.format_number(metrics['total_accidents']))

        # Main content
        col_map, col_stats = st.columns([2, 1])
        
        with col_map:
            # Year selector
            year = st.selectbox(
                'Select Year:',
                sorted(self.df['ACCIDENT_YEAR'].unique()),
                index=len(self.df['ACCIDENT_YEAR'].unique()) - 1
            )
            
            # Create and display map using streamlit-folium
            st_map = self.create_map(year)
            st_folium(st_map, width=900, height=500)

        with col_stats:
            st.markdown("<h3 style='color: #FF00FF;'>Zone Statistics</h3>", unsafe_allow_html=True)
            
            # Zone statistics
            year_data = self.df[self.df['ACCIDENT_YEAR'] == year]
            zone_counts = year_data['ZONE'].value_counts().sort_values(ascending=False).head(8)
            
            for zone, count in zone_counts.items():
                zone_name = self.zone_names.get(str(zone), f'Zone {zone}')
                st.markdown(f"""
                <div style='
                    margin-bottom: 10px;
                    padding: 8px;
                    background-color: rgba(255, 0, 255, 0.1);
                    border-radius: 5px;
                '>
                    <div style='color: #00FFFF;'>{zone_name}</div>
                    <div style='font-size: 0.9em;'>Accidents: {count}</div>
                </div>
                """, unsafe_allow_html=True)

        # Additional visualizations
        st.markdown("<h3 style='color: #FF00FF; margin-top: 20px;'>Additional Insights</h3>", unsafe_allow_html=True)
        
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            # Severity by category
            category = st.selectbox(
                'Select Category:',
                ['NATIONALITY_GROUP_OF_ACCIDENT_', 'ACCIDENT_NATURE', 'ACCIDENT_REASON'],
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            severity_counts = self.df.groupby([category, 'ACCIDENT_SEVERITY']).size().unstack().fillna(0)
            fig_severity = px.bar(
                severity_counts, 
                barmode='stack',
                title='Accident Severity by ' + category.replace('_', ' ').title()
            )
            fig_severity.update_layout(
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background'],
                font_color=self.colors['text']
            )
            st.plotly_chart(fig_severity, use_container_width=True)

        with viz_col2:
            # Age scatter plot
            year_data = self.df[self.df['ACCIDENT_YEAR'] == year]
            year_data['AGE'] = year_data['BIRTH_YEAR_OF_ACCIDENT_PERPETR'].apply(
                lambda x: year - x if pd.notnull(x) else None
            )
            year_data = year_data[(year_data['AGE'] >= 0) & (year_data['AGE'] <= 90)]
            age_counts = year_data.groupby('AGE').size().reset_index(name='ACCIDENT_COUNT')
            mean_age = year_data['AGE'].mean()
            
            fig_age = px.scatter(
                age_counts,
                x='AGE',
                y='ACCIDENT_COUNT',
                size='ACCIDENT_COUNT',
                title='Age vs Number of Accidents'
            )
            fig_age.add_annotation(
                xref="paper", yref="paper",
                x=0.95, y=1.05,
                text=f"Mean Age: {mean_age:.1f}",
                showarrow=False,
                font=dict(size=12, color=self.colors['text']),
                align="right"
            )
            fig_age.update_layout(
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background'],
                font_color=self.colors['text']
            )
            st.plotly_chart(fig_age, use_container_width=True)

if __name__ == "__main__":
    dashboard = QatarAccidentsStreamlit()
    dashboard.run_dashboard()