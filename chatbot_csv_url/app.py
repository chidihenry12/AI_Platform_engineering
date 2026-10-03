import streamlit as st
from backend import ingest_csv, crawl_website, index_data
import pandas as pd

st.set_page_config(page_title="Doc Chatbot", layout="centered")
st.markdown("""
    <style>
    .chat-container {display: flex; flex-direction: column; gap: 12px; margin-bottom: 1.5em;}
    .bubble-user {
        align-self: flex-end;
        background: #dcf8c6;
        color: #222;
        border-radius: 16px 16px 4px 16px;
        padding: 10px 16px;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-right: 8px;
    }
    .bubble-ai {
        align-self: flex-start;
        background: #e9e9eb;
        color: #222;
        border-radius: 16px 16px 16px 4px;
        padding: 10px 16px;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-left: 8px;
    }
    .chat-label {font-weight: bold; font-size: 0.95em; margin-bottom: 2px; display: flex; align-items: center;}
    .icon {margin-right: 6px;}
    </style>
""", unsafe_allow_html=True)

st.title("📄Document Chatbot - Wesite URL chatbot")

st.sidebar.header("Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
url = st.sidebar.text_input("Enter Website URL")

if 'doc_context' not in st.session_state:
    st.session_state['doc_context'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'data_type' not in st.session_state:
    st.session_state['data_type'] = None
if 'csv_info' not in st.session_state:
    st.session_state['csv_info'] = None
if 'web_snippet' not in st.session_state:
    st.session_state['web_snippet'] = None

# Ingest document
if uploaded_file:
    df = ingest_csv(uploaded_file)
    st.session_state['doc_context'] = df.to_csv(index=False)
    st.session_state['data_type'] = 'csv'
    st.session_state['csv_info'] = {
        'shape': df.shape,
        'columns': list(df.columns),
        'preview': df.head().to_dict()
    }
    st.sidebar.success("CSV uploaded and indexed!")
elif url:
    with st.spinner("Crawling website..."):
        text = crawl_website(url)
        st.session_state['doc_context'] = text
        st.session_state['data_type'] = 'web'
        st.session_state['web_snippet'] = text[:500]
        st.sidebar.success("Website crawled and indexed!")

# Data details section
if st.session_state['doc_context']:
    st.subheader("Data Details")
    if st.session_state['data_type'] == 'csv' and st.session_state['csv_info']:
        info = st.session_state['csv_info']
        st.write(f"**CSV Shape:** {info['shape']}")
        st.write(f"**Columns:** {info['columns']}")
        st.write("**Preview:**")
        st.dataframe(pd.DataFrame(info['preview']))
    elif st.session_state['data_type'] == 'web' and st.session_state['web_snippet']:
        st.write("**Website Text Snippet:**")
        st.code(st.session_state['web_snippet'])

    # Custom chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state['chat_history']:
        if msg['role'] == 'user':
            st.markdown(
                f"""
                <div class="bubble-user">
                    <div class="chat-label"><span class="icon">🧑‍💻</span>You</div>
                    <div>{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Format AI output: show only answer, handle errors and formatted output
            ai_content = ""
            if isinstance(msg['content'], dict):
                if 'processor_output' in msg['content']:
                    ai_content = msg['content']['processor_output']
                elif 'processor_raw_response' in msg['content']:
                    ai_content = msg['content']['processor_raw_response']
                elif 'processor_error' in msg['content']:
                    ai_content = f"<span style='color:red'>AI Error: {msg['content']['processor_error']}</span>"
                elif 'error' in msg['content']:
                    ai_content = f"<span style='color:red'>AI Error: {msg['content']['error']}</span>"
                else:
                    ai_content = str(msg['content'])
            else:
                ai_content = str(msg['content'])
            st.markdown(
                f"""
                <div class="bubble-ai">
                    <div class="chat-label"><span class="icon">🤖</span>AI</div>
                    <div>{ai_content}</div>
                </div>
                """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    user_input = st.chat_input("Type your message...")
    if user_input:
        st.session_state['chat_history'].append({'role': 'user', 'content': user_input})
        with st.spinner("AI is typing..."):
            ai_response = index_data(f"Context: {st.session_state['doc_context']}\nUser: {user_input}")
        st.session_state['chat_history'].append({'role': 'bot', 'content': ai_response})
        st.rerun()
else:
    st.info("Upload a CSV or enter a website URL to begin chatting.") 