import streamlit as st

st.set_page_config(page_title="RAG Chatbot Cơ Khí", layout="wide")

page = st.sidebar.radio("Chuyển trang", ["Chatbot Hỏi Đáp", "Tiến Trình Ingest", "Duyệt Tài Liệu"])

if page == "Chatbot Hỏi Đáp":
    import app_chatbot
    app_chatbot.run_chat()
elif page == "Tiến Trình Ingest":
    import app_queue
    app_queue.run_queue()
elif page == "Duyệt Tài Liệu":
    import app_admin
    app_admin.run_admin()
