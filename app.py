import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from acc import QatarAccidentsStreamlit

# Load CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session state for navigation
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def show_page(page_name):
    st.session_state.page = page_name

# Pages
def home_page():
    st.markdown('<h1 class="page-title">TraffiQ</h1>', unsafe_allow_html=True)
    st.markdown('<h3 class="page-title">Traffic Intelligence for Qatar</h3>', unsafe_allow_html=True)

    # Chat Interface
    with st.container():
        user_input = st.chat_input("Ask anything about traffic data...")

    # Analytics Buttons Grid
    cols = st.columns(5)
    buttons = [
        ("Accidents", "🚑", "accidents"),
        ("Violations", "🚔", "violations"),
        ("License", "📇", "license"),
        ("Vehicle", "🚗", "vehicle"),
        ("Environment", "🌳", "environment")
    ]
    
    for col, (label, icon, page) in zip(cols, buttons):
        with col:
            if st.button(f"{icon} {label}", key=f"btn_{page}", 
                        use_container_width=True,
                        help=f"View {label} Analytics"):
                show_page(page)

    # Key Stats Grid
    st.header("Key Statistics")
    stats_cols = st.columns(4)
    metrics = [("Total Accidents", "12,345"), ("Daily Violations", "892"), 
              ("Licenses Issued", "3,451"), ("CO2 Saved (tons)", "45,678")]
    
    for col, (label, value) in zip(stats_cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric">
                <h3>{label}</h3>
                <h1>{value}</h1>
            </div>
            """, unsafe_allow_html=True)

    # Dashboard Sections
    tab_labels = [f"{icon} {label}" for (label, icon, _) in buttons]
    tabs = st.tabs(tab_labels)
    
    # Generate Sample Plots
    for i, tab in enumerate(tabs):
        with tab:
            fig = go.Figure()
            x = ['2020', '2021', '2022', '2023']
            y = np.random.randint(1000, 5000, size=4)
            
            fig.add_trace(go.Bar(
                x=x, y=y,
                marker_color='#00f7ff',
                marker_line_color='#00f7ff',
                marker_line_width=1
            ))
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#00f7ff',
                title=f"{buttons[i][0]} Trends",
                xaxis_title="Year",
                yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Feedback Section
    st.header("Feedback & Trivia")
    with st.expander("Test Your Knowledge"):
        q1 = st.radio("Q1: Qatar has zero road fatalities in 2022", ["Fact", "Fiction"])
        q2 = st.radio("Q2: Doha has smart traffic light system", ["Fact", "Fiction"])
        q3 = st.radio("Q3: Electric vehicles are tax-free in Qatar", ["Fact", "Fiction"])

def accidents_page():
    st.markdown('<h1 class="page-title">Accidents Analytics</h1>', unsafe_allow_html=True)
    if st.button("← Back to Home"):
        show_page('home')
    # Initialize and run the dashboard from acc.py
    dashboard = QatarAccidentsStreamlit()
    dashboard.run_dashboard()

def violations_page():
    st.markdown('<h1 class="page-title">Violations Analytics</h1>', unsafe_allow_html=True)
    if st.button("← Back to Home"):
        show_page('home')
    # Add your violations analysis content here

# Add similar functions for other pages...

def main():
    # Page routing
    if st.session_state.page == 'home':
        home_page()
    elif st.session_state.page == 'accidents':
        accidents_page()
    elif st.session_state.page == 'violations':
        violations_page()
    # Add other page conditions...

if __name__ == "__main__":
    main()
