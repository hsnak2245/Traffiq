import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.metrics.pairwise import cosine_similarity
import json

# Set page config
st.set_page_config(
    page_title="Qatar Traffic Violation Analysis",
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
    .stSelectbox label, .stSlider label {
        color: #FF00FF !important;
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

# Helper functions
def load_json_data(filename):
    """Load data from JSON file and clean it"""
    with open(filename, 'r') as f:
        data = json.load(f)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Fill NaN values with 0 for numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df[numeric_columns] = df[numeric_columns].fillna(0)
    
    return df

def create_fingerprint(df):
    """Create violation fingerprints"""
    violation_cols = [
        'lsr_lzy_d_lrdr_over_speed_radar',
        'mkhlft_qt_lshr_ldwy_y_passing_traffic_signal_violations',
        'mkhlft_lrshdt_walt_ltnbyh_guidlines_and_alarm_signals_violations',
        'mkhlft_llwht_lm_dny_metallic_plates_violations',
        'mkhlft_ltjwz_overtaking_violations',
        'mkhlft_tsjyl_w_dm_tjdyd_lstmr_registration_and_form_non_renewal_violations',
        'mkhlft_rkhs_lqyd_driving_licenses_violations',
        'mkhlft_lhrk_lmrwry_traffic_movement_violations',
        'mkhlft_qw_d_wltzmt_lwqwf_wlntzr_stand_and_wait_rules_and_obligations_violations',
        'khr_other'
    ]
    
    # Ensure all required columns exist
    missing_cols = [col for col in violation_cols if col not in df.columns]
    if missing_cols:
        for col in missing_cols:
            df[col] = 0
    
    # Calculate fingerprints
    fingerprints = df[violation_cols].div(df['mjmw_lmkhlft_lmrwry_total_traffic_violations'], axis=0)
    
    # Replace any infinite values with 0
    fingerprints = fingerprints.replace([np.inf, -np.inf], 0)
    
    # Fill any remaining NaN values with 0
    fingerprints = fingerprints.fillna(0)
    
    return fingerprints

# Friendly names mapping
violation_names = {
    'lsr_lzy_d_lrdr_over_speed_radar': 'Over Speed (Radar)',
    'mkhlft_qt_lshr_ldwy_y_passing_traffic_signal_violations': 'Traffic Signal',
    'mkhlft_lrshdt_walt_ltnbyh_guidlines_and_alarm_signals_violations': 'Guidelines & Alarms',
    'mkhlft_llwht_lm_dny_metallic_plates_violations': 'Metallic Plates',
    'mkhlft_ltjwz_overtaking_violations': 'Overtaking',
    'mkhlft_tsjyl_w_dm_tjdyd_lstmr_registration_and_form_non_renewal_violations': 'Registration',
    'mkhlft_rkhs_lqyd_driving_licenses_violations': 'Licenses',
    'mkhlft_lhrk_lmrwry_traffic_movement_violations': 'Traffic Movement',
    'mkhlft_qw_d_wltzmt_lwqwf_wlntzr_stand_and_wait_rules_and_obligations_violations': 'Parking',
    'khr_other': 'Other'
}

# App title
st.title("🚗 Qatar Traffic Violation Pattern Analysis")

try:
    # Load and prepare data
    with st.spinner('Loading data...'):
        df = load_json_data('viola.json')
        df['month'] = pd.to_datetime(df['month'])
        df = df.sort_values('month')
        fingerprints = create_fingerprint(df)
        similarity_matrix = cosine_similarity(fingerprints)

    # Create two columns for the dropdowns
    col1, col2 = st.columns(2)

    with col1:
        # Violation type selector for line chart
        selected_violation = st.selectbox(
            'Select Violation Type for Line Chart:',
            options=list(violation_names.keys()),
            format_func=lambda x: violation_names[x]
        )

    with col2:
        # Month selector for Pareto chart
        month_options = [date.strftime('%B %Y') for date in df['month']]
        selected_month_idx = st.selectbox(
            'Select Month for Pattern Analysis:',
            options=range(len(month_options)),
            format_func=lambda x: month_options[x]
        )

    # Monthly Violation Line Chart
    st.subheader('Monthly Violation Line Chart')
    monthly_data = df.groupby([df['month'].dt.year, df['month'].dt.month])[selected_violation].sum().unstack(level=0)
    fig_line = px.line(monthly_data, title=f'Monthly {violation_names[selected_violation]} Violations')
    fig_line.update_traces(line=dict(width=4, shape='spline'))
    fig_line.update_layout(
        xaxis=dict(
            title='Month',
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ),
        yaxis_title='Number of Violations',
        plot_bgcolor='black',
        paper_bgcolor='black',
        font_color='white'
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Create two columns for Pareto chart and similarity results
    col3, col4 = st.columns(2)

    with col3:
        # Pareto Chart
        st.subheader('Violation Pattern Pareto Chart')
        selected_fingerprint = fingerprints.iloc[selected_month_idx]
        sorted_fingerprint = selected_fingerprint.sort_values(ascending=False)
        
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=[violation_names[col] for col in sorted_fingerprint.index],
            y=sorted_fingerprint.values * 100,
            marker_color='#FF00FF'
        ))
        
        fig_pareto.update_layout(
            title=f"Violation Pattern for {month_options[selected_month_idx]}",
            xaxis_title='Violation Type',
            yaxis_title='Percentage (%)',
            plot_bgcolor='black',
            paper_bgcolor='black',
            font_color='white'
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

    with col4:
        # Similarity Results
        st.subheader('Pattern Similarity Results')
        similarities = similarity_matrix[selected_month_idx]
        similarity_df = pd.DataFrame({
            'Month': df['month'].dt.strftime('%B %Y'),
            'Similarity': similarities * 100
        })
        similarity_df = similarity_df.sort_values('Similarity', ascending=False).head(4)  # Display only top 4
        
        for _, row in similarity_df.iterrows():
            st.markdown(f"""
                <div style='
                    background-color: #111111;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #333;
                    margin-bottom: 5px;
                '>
                    <h4 style='margin: 0; color: white;'>{row['Month']}</h4>
                    <p style='margin: 0; color: white;'>Similarity: {row['Similarity']:.2f}%</p>
                </div>
            """, unsafe_allow_html=True)

    # Insights section
    st.subheader('📊 Insights')
    st.write("""
        This visualization reveals the 'fingerprint' of traffic violations for each month. 
        The Pareto chart shows the proportion of each violation type, while the similarity results 
        help identify months with similar violation patterns, regardless of total volume.
    """)
    
    st.markdown("""
        **Key features to look for:**
        - Dominant violation types (longer bars in the Pareto chart)
        - Seasonal patterns (similar months across years)
        - Unusual months (low similarity with others)
        - Long-term changes in violation patterns
    """)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")