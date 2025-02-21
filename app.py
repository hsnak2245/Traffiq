import streamlit as st
import pandas as pd
from groq import Groq

# Initialize Groq client
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
groq_client = Groq(api_key=GROQ_API_KEY)

# Load CSS
st.markdown("""
<style>
.page-title {
    font-family: 'Arial', sans-serif;
    color: #333;
    text-align: center;
    margin-top: 20px;
    margin-bottom: 30px;
}

.button-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
    margin-bottom: 30px;
}

.stButton button {
    width: 100%;
    padding: 20px;
    font-size: 1.2em;
    background-color: #f0f2f6;
    border: none;
    border-radius: 10px;
    transition: all 0.3s ease;
}

.stButton button:hover {
    background-color: #e0e2e6;
    transform: translateY(-2px);
}

.chat-container {
    margin-top: 30px;
    padding: 20px;
    border-radius: 10px;
    background-color: #f9f9f9;
}

.user-message {
    background-color: #e3f2fd;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}

.bot-message {
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}

.ai-response {
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 10px;
    margin-top: 10px;
    border-left: 4px solid #2196F3;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Load simulated knowledge base
@st.cache_data
def load_knowledge_base():
    # In a real implementation, this would load from info.txt
    # For now, we'll use a DataFrame to simulate the knowledge base
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
        # Load knowledge base
        social_updates_df = load_knowledge_base()
        
        # Find relevant context
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
            return f"AI processing error: {str(e)}"
            
    except Exception as e:
        return f"Error processing query: {str(e)}"

def home_page():
    st.markdown('<h1 class="page-title">TraffiQ</h1>', unsafe_allow_html=True)
    st.markdown('<h3 class="page-title">Traffic Intelligence for Qatar</h3>', unsafe_allow_html=True)

    # 2x2 Button Grid
    col1, col2 = st.columns(2)
    buttons = [
        ("Accidents 🚑", "accidents", "https://accidents.streamlit.app/"),
        ("Violations 🚔", "violations", "https://violations.streamlit.app/"),
        ("License 📇", "license", "https://license.streamlit.app/"),
        ("Vehicle 🚗", "vehicle", "https://vehicle.streamlit.app/")
    ]
    
    for i, (label, page, link) in enumerate(buttons):
        with col1 if i < 2 else col2:
            if st.button(label, key=f"btn_{page}", use_container_width=True):
                st.markdown(f'<script>window.open("{link}", "_blank");</script>', unsafe_allow_html=True)

    # Chat Interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown("### Traffic Safety Assistant")
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input("Ask about Qatar traffic data, safety measures, or policy recommendations...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Process query with RAG and get response
        with st.spinner("Processing..."):
            response = process_query_with_rag(user_input)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        st.experimental_rerun()

def main():
    if st.session_state.page == 'home':
        home_page()

if __name__ == "__main__":
    main()