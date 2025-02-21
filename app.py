import streamlit as st
import pandas as pd
from groq import Groq

# Initialize Groq client
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
groq_client = Groq(api_key=GROQ_API_KEY)

# Configure page
st.set_page_config(
    page_title="TraffiQ",
    page_icon="🚦",
    layout="wide"
)

# Load CSS with updated styling
# Update the CSS section with this improved styling
st.markdown("""
<style>
/* Main container */
.main {
    background: #0a0e1a;
    color: #e0e0e0;
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

/* Title styling */
.page-title {
    font-family: 'Space Grotesk', sans-serif;
    background: linear-gradient(45deg, #00d2ff, #3a7bd5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin: 2rem 0 3rem 0;
    font-size: 3.5rem;
    font-weight: 700;
    letter-spacing: -1px;
}

/* Button grid styling */
.button-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 0 1rem;
}

.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-bottom: 1.5rem !important;
    height: auto !important;
    min-height: 100px;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    background: linear-gradient(135deg, #3498db 0%, #2c3e50 100%) !important;
}

/* Chat container styling */
.chat-container {
    padding: 2rem;
    margin: 3rem auto;
    max-width: 800px;
    background: rgba(16, 22, 36, 0.8);
    border-radius: 24px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.chat-title {
    color: #00d2ff;
    font-size: 1.5rem;
    margin-bottom: 2rem;
    font-weight: 600;
    text-align: center;
    letter-spacing: -0.5px;
}

.user-message {
    background: rgba(42, 157, 244, 0.15);
    color: white;
    padding: 1.2rem 1.5rem;
    border-radius: 18px;
    margin: 1.5rem 0;
    border: 1px solid rgba(42, 157, 244, 0.3);
    backdrop-filter: blur(5px);
    line-height: 1.6;
}

.bot-message {
    background: rgba(78, 205, 196, 0.15);
    color: white;
    padding: 1.2rem 1.5rem;
    border-radius: 18px;
    margin: 1.5rem 0;
    border: 1px solid rgba(78, 205, 196, 0.3);
    backdrop-filter: blur(5px);
    line-height: 1.6;
}

/* Chat input styling */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.05) !important;
    color: white !important;
    border: 2px solid rgba(78, 205, 196, 0.3) !important;
    border-radius: 16px !important;
    padding: 1.2rem !important;
    font-size: 1.1rem !important;
    transition: all 0.3s ease;
}

.stTextInput > div > div > input:focus {
    border-color: #00d2ff !important;
    box-shadow: 0 0 0 3px rgba(0, 210, 255, 0.2) !important;
}

/* Improved spacing and typography */
body {
    line-height: 1.6;
    font-family: 'Inter', sans-serif;
}

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

/* Status indicators */
.status-indicator {
    padding: 0.5rem 1rem;
    background: rgba(78, 205, 196, 0.2);
    border-radius: 8px;
    display: inline-block;
    margin: 0.5rem 0;
    font-size: 0.9rem;
}

/* Section dividers */
.section-divider {
    border: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(78, 205, 196, 0.4), transparent);
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)
# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

@st.cache_data
def load_knowledge_base():
    data = {
        'message': [
            "Qatar recorded a 15% decrease in traffic accidents in urban areas after implementing smart traffic systems.",
            "Recent policy changes require mandatory defensive driving courses for new license applicants in Qatar.",
            "Traffic safety indicators show peak accident times between 7-9 AM and 4-6 PM in major Qatar cities.",
            "New traffic policy focuses on reducing accidents through AI-powered traffic management and stricter enforcement.",
            "Qatar's road safety campaign resulted in 25% reduction in pedestrian accidents in residential areas.",
        ]
    }
    return pd.DataFrame(data)

def process_query_with_rag(query):
    try:
        social_updates_df = load_knowledge_base()
        relevant_updates = social_updates_df[
            social_updates_df['message'].str.contains('|'.join(query.split()), case=False, na=False)
        ]
        
        context = "\n".join(relevant_updates['message'].tolist())
        
        messages = [
            {"role": "system", "content": """You are TraffiQ, an AI traffic expert and statistician for Qatar. 
             Your role is to:
             1. Analyze traffic patterns and accident data
             2. Provide policy recommendations based on data
             3. Promote road safety and best practices
             4. Guide policymakers with data-driven insights
             
             Provide clear, accurate information based on available data."""},
            {"role": "user", "content": f"Context from traffic database:\n{context}\n\nUser Question: {query}"}
        ]
        
        try:
            response = groq_client.chat.completions.create(
                messages=messages,
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=500,
                top_p=0.9
            )
            return response.choices[0].message.content
        except Exception as e:
            return "I apologize, but I'm having trouble connecting to the AI service. Please try again in a moment."
            
    except Exception as e:
        return "I apologize, but I encountered an error processing your query. Please try again."

def home_page():
    st.markdown('<h1 class="page-title">TraffiQ</h1>', unsafe_allow_html=True)
    # Removed subtitle

    # Create a container for better spacing
    with st.container():
        # Add the button-container class for centered, constrained width
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        
        # 2x2 Button Grid
        col1, col2 = st.columns(2)
        
        buttons = [
            ("🚑 Accidents", "accidents", "https://accidents.streamlit.app/"),
            ("🚔 Violations", "violations", "https://violations.streamlit.app/"),
            ("📇 License", "license", "https://license.streamlit.app/"),
            ("🚗 Vehicle", "vehicle", "https://vehicle.streamlit.app/")
        ]
        
        for i, (label, page, link) in enumerate(buttons):
            with col1 if i % 2 == 0 else col2:
                if st.button(label, key=f"btn_{page}"):
                    st.markdown(f'<script>window.open("{link}", "_blank");</script>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Chat Interface
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        st.markdown('<div class="chat-title">🤖 Traffic Safety Assistant</div>', unsafe_allow_html=True)
        
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)

        # Chat input
        user_input = st.chat_input("Ask about Qatar traffic data, safety measures, or policy recommendations...")
        
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.spinner("Analyzing your query..."):
                response = process_query_with_rag(user_input)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    if st.session_state.page == 'home':
        home_page()

if __name__ == "__main__":
    main()