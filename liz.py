import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging
from datetime import datetime

class LicenseDashboard:
    def __init__(self, license_file='liz.csv'):
        self.license_file = license_file
        self.license_df = None
        self.colors = {
            'background': '#000000',
            'text': '#FFFFFF',
            'neon_pink': '#FF00FF',
            'neon_cyan': '#00FFFF',
            'neon_green': '#39FF14',
            'neon_blue': '#0000FF',
            'maroon': '#800000'
        }
        self.load_data()
    
    def load_data(self):
        try:
            self.license_df = pd.read_csv(self.license_file, skipinitialspace=True)
            self.license_df['FIRST_ISSUEDATE'] = pd.to_datetime(self.license_df['FIRST_ISSUEDATE'])
            self.license_df['AGE'] = self.license_df['FIRST_ISSUEDATE'].dt.year - self.license_df['BIRTHYEAR']
            self.license_df['MONTH'] = self.license_df['FIRST_ISSUEDATE'].dt.month
            self.license_df['YEAR'] = self.license_df['FIRST_ISSUEDATE'].dt.year
        except Exception as e:
            logging.error("Error loading data: %s", e)
            st.error("Error loading data. Please check the log file for details.")
    
    def create_license_line_chart(self, selected_category, selected_year):
        if selected_category not in self.license_df.columns:
            return None

        try:
            license_counts = self.license_df[self.license_df['YEAR'] == selected_year].groupby(
                [selected_category, pd.Grouper(key='FIRST_ISSUEDATE', freq='W')]
            ).size().reset_index(name='COUNT')

            fig = px.line(
                license_counts, 
                x='FIRST_ISSUEDATE', 
                y='COUNT', 
                color=selected_category,
                title=f'License Issued by {selected_category} in {selected_year}'
            )
            fig.update_traces(line=dict(width=3, shape='spline'))
            fig.update_layout(
                xaxis_title='Issue Date',
                yaxis_title='Number of Licenses',
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background'],
                font_color=self.colors['text']
            )
            return fig
        except Exception as e:
            logging.error(f"Error creating line chart: {e}")
            return None

    def create_age_bubble_chart(self):
        try:
            age_counts = self.license_df.groupby('AGE').size().reset_index(name='COUNT')
            mean_age = self.license_df['AGE'].mean()

            fig = px.scatter(
                age_counts, 
                x='AGE', 
                y='COUNT', 
                size='COUNT',
                color_discrete_sequence=[self.colors['neon_blue']]
            )
            fig.add_annotation(
                x=0.95, y=0.95,
                xref='paper', yref='paper',
                text=f'Mean Age: {mean_age:.2f}',
                showarrow=False,
                font=dict(color=self.colors['neon_green'], size=14),
                bgcolor=self.colors['background']
            )
            fig.update_layout(
                xaxis_title='Age at License Issue',
                yaxis_title='Number of Licenses Issued',
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background'],
                font_color=self.colors['text']
            )
            return fig
        except Exception as e:
            logging.error(f"Error creating bubble chart: {e}")
            return None

    def create_annual_license_chart(self):
        try:
            monthly_counts = self.license_df.groupby(['YEAR', 'MONTH']).size().reset_index(name='COUNT')
            
            fig = px.line(
                monthly_counts, 
                x='MONTH', 
                y='COUNT', 
                color='YEAR', 
                title='Annual License Issue'
            )
            fig.update_traces(line=dict(width=3, shape='spline'))
            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=list(range(1, 13)),
                    ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                ),
                xaxis_title='Month',
                yaxis_title='Number of Licenses Issued',
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background'],
                font_color=self.colors['text']
            )
            return fig
        except Exception as e:
            logging.error(f"Error creating annual license chart: {e}")
            return None

    def run_dashboard(self):
        # Set page config
        st.set_page_config(
            page_title="TraffiQ",
            page_icon="🚗",
            layout="wide"
        )

        # Custom CSS
        st.markdown("""
        <style>
        .stApp {
            background-color: black;
            color: white;
        }
        .stSelectbox {
            color: black;
        }
        h1, h2, h3 {
            color: #00FFFF;
        }
        .home-button {
            background-color: #FF00FF;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
        }
        .home-button:hover {
            background-color: #00FFFF;
        }
        </style>
        """, unsafe_allow_html=True)

        # Home button
        st.markdown("""
        <a href="https://traffiq.streamlit.app/" class="home-button">Home</a>
        """, unsafe_allow_html=True)

        # Title
        st.title("TraffiQ")
        st.markdown("### License Dashboard")

        # Create columns for filters
        col1, col2 = st.columns(2)
        with col1:
            selected_category = st.selectbox(
                "Select Category",
                options=['GENDER', 'NATIONALITY_GROUP'],
                key='category'
            )
        with col2:
            selected_year = st.selectbox(
                "Select Year",
                options=sorted(self.license_df['YEAR'].unique()),
                key='year'
            )

        # Create three columns for charts
        col1, col2 = st.columns(2)

        # Annual License Issue
        with col1:
            st.markdown("### Annual License Issue")
            annual_chart = self.create_annual_license_chart()
            if annual_chart:
                st.plotly_chart(annual_chart, use_container_width=True)

        # Age Bubble Chart
        with col2:
            st.markdown("### Age at License Issue")
            bubble_chart = self.create_age_bubble_chart()
            if bubble_chart:
                st.plotly_chart(bubble_chart, use_container_width=True)

        # License by Category (Full Width)
        st.markdown("### License Issued by Category")
        category_chart = self.create_license_line_chart(selected_category, selected_year)
        if category_chart:
            st.plotly_chart(category_chart, use_container_width=True)

if __name__ == "__main__":
    dashboard = LicenseDashboard()
    dashboard.run_dashboard()