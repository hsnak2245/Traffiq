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
st.markdown("""
<style>
/* Main container */
.main {
    background: linear-gradient(135deg, #1a1f2e 0%, #2d1f3d 100%);
    color: white;
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

/* Title styling */
.page-title {
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    background: linear-gradient(120deg, #ff6b6b, #4ecdc4);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    text-align: center;
    margin: 2rem 0;
    font-size: 4rem;
    font-weight: 800;
    letter-spacing: -1px;
}

.subtitle {
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #a0aec0;
    text-align: center;
    margin-bottom: 3rem;
    font-size: 1.5rem;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}

/* Button grid styling */
.button-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 0 1rem;
}

.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(78, 205, 196, 0.1) 100%) !important;
    color: white !important;
    border: 2px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 16px !important;
    padding: 1.8rem !important;
    font-size: 1.3rem !important;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stButton > button:hover {
    background: linear-gradient(135deg, rgba(255, 107, 107, 0.2) 0%, rgba(78, 205, 196, 0.2) 100%) !important;
    border-color: rgba(255, 255, 255, 0.4) !important;
    transform: translateY(-3px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

/* Chat container styling */
.chat-container {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.08) 100%);
    border-radius: 20px;
    padding: 2.5rem;
    margin: 3rem auto;
    max-width: 800px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.chat-title {
    color: #4ecdc4;
    font-size: 1.8rem;
    margin-bottom: 2rem;
    font-weight: 700;
    text-align: center;
}

.user-message {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
    color: white;
    padding: 1.2rem;
    border-radius: 16px;
    margin: 1rem 0;
    border: 1px solid rgba(59, 130, 246, 0.2);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.bot-message {
    background: linear-gradient(135deg, rgba(78, 205, 196, 0.1) 0%, rgba(255, 107, 107, 0.1) 100%);
    color: white;
    padding: 1.2rem;
    border-radius: 16px;
    margin: 1rem 0;
    border: 1px solid rgba(78, 205, 196, 0.2);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
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
    border-color: rgba(78, 205, 196, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.2) !important;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: rgba(78, 205, 196, 0.5);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(78, 205, 196, 0.7);
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
    st.markdown('<p class="subtitle">Intelligent Traffic Management System for Qatar</p>', unsafe_allow_html=True)

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