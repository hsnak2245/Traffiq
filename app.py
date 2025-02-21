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

/* Import Space Grotesk */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&display=swap');

/* Title styling */
.page-title {
    font-family: 'Space Grotesk', sans-serif;
    color: #4ecdc4;
    text-align: center;
    margin: 2rem 0 3rem 0;
    font-size: 4.5rem;
    font-weight: 700;
}

@keyframes neon {
    from {
        text-shadow: 
            0 0 7px #4ecdc4,
            0 0 10px #4ecdc4,
            0 0 21px #4ecdc4,
            0 0 42px rgba(78, 205, 196, 0.5);
    }
    to {
        text-shadow: 
            0 0 10px #4ecdc4,
            0 0 15px #4ecdc4,
            0 0 25px #4ecdc4,
            0 0 45px rgba(78, 205, 196, 0.5);
    }
}

/* Button container styling */
.button-container {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin: 0 auto;
    padding: 0 1rem;
    flex-wrap: wrap; /* Ensure buttons wrap if they overflow */
}

.stButton > button {
    width: auto !important;
    background-color: #2C3E50 !important;
    color: #4ecdc4 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.8rem 1.2rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    margin-bottom: 1rem !important;
    height: auto !important;
    display: inline-block; /* Ensure buttons are inline */
}

.stButton > button:hover {
    background-color: #34495E !important;
    color: #5ddbcf !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25);
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
    width: 50%; 
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
    width: 50%;
    border-radius: 16px;
    margin: 1rem 0;
    border: 1px solid rgba(78, 205, 196, 0.2);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* Chat container styling */
.chat-container {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
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
                max_tokens=6000,
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
        
        # Single row of buttons
        buttons = [
            ("🚑 Accidents", "accidents", "https://accidents.streamlit.app/"),
            ("🚔 Violations", "violations", "https://violations.streamlit.app/"),
            ("📇 License", "license", "https://license.streamlit.app/"),
            ("🚗 Vehicle", "vehicle", "https://vehicle.streamlit.app/")
        ]
        
        for label, page, link in buttons:
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