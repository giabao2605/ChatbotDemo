import streamlit as st
import auth

st.set_page_config(page_title="RAG Chatbot Cơ Khí", layout="wide")

auth.check_auth()
user = auth.get_current_user()

if user is None:
    st.stop()

st.sidebar.markdown(f"**Xin chào, {user['display_name']}!**")
st.sidebar.caption(f"Phòng ban: {user['department']}")

if st.sidebar.button("Đăng xuất"):
    auth.logout()

menu_options = ["Chatbot Hỏi Đáp"]

if auth.has_role("uploader") or auth.has_role("admin"):
    menu_options.append("Tiến Trình Ingest")

if auth.has_role("reviewer") or auth.has_role("admin"):
    menu_options.append("Duyệt Tài Liệu")

# Cho phép điều hướng bằng code (ví dụ nút "Thêm file mới" ở trang Duyệt Tài Liệu)
if "_goto_page" in st.session_state:
    _target = st.session_state.pop("_goto_page")
    if _target in menu_options:
        st.session_state["nav_page"] = _target

page = st.sidebar.radio("Chuyển trang", menu_options, key="nav_page")

if page == "Chatbot Hỏi Đáp":
    import app_chatbot
    app_chatbot.run_chat()

elif page == "Tiến Trình Ingest":
    import app_queue
    app_queue.run_queue()

elif page == "Duyệt Tài Liệu":
    import app_admin
    app_admin.run_admin()
