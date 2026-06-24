import os
import streamlit as st
import auth
from db_logic import engine


def run_settings():
    st.title("Cấu hình hệ thống")
    if not auth.has_role("admin"):
        st.error("Chỉ admin được truy cập cấu hình.")
        return

    st.subheader("RAG")
    rag_server_url = os.getenv("RAG_SERVER_URL", "")
    if rag_server_url:
        st.success("Đang dùng RAG Server API")
        st.code(rag_server_url)
    else:
        st.warning("Chưa có RAG_SERVER_URL. Hệ thống sẽ dùng subprocess worker.")
    st.write("**MAX_CONCURRENT_RAG:**", os.getenv("MAX_CONCURRENT_RAG", "2"))
    st.write("**RAG_WORKER_TIMEOUT:**", os.getenv("RAG_WORKER_TIMEOUT", "240"))

    st.subheader("Database")
    if engine is None:
        st.error("Không kết nối được database.")
    else:
        st.success("Database engine đã khởi tạo.")

    st.subheader("Bảo mật")
    st.info("Trang này không hiển thị API key, password database hoặc token.")
