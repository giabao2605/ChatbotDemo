import streamlit as st
import auth
import ui_theme

st.set_page_config(page_title="Trợ Lý Kỹ Thuật Cơ Khí", layout="wide", initial_sidebar_state="expanded")
ui_theme.inject_global_css()

auth.check_auth()
user = auth.get_current_user()
if user is None:
    st.stop()


def can_access_page(allowed_roles):
    if not allowed_roles:
        return True
    roles = user.get("roles", [])
    if "admin" in roles:
        return True
    return any(role in roles for role in allowed_roles)


PAGES = [
    {"key": "dashboard", "label": "Tổng quan", "roles": ["admin"]},
    {"key": "chatbot", "label": "Chatbot hỏi đáp", "roles": ["viewer", "uploader", "reviewer", "admin"]},
    {"key": "upload", "label": "Tải tài liệu", "roles": ["uploader", "admin"]},
    {"key": "queue", "label": "Tiến trình ingest", "roles": ["uploader", "admin"]},
    {"key": "review", "label": "Duyệt tài liệu", "roles": ["reviewer", "admin"]},
    {"key": "documents", "label": "Kho tài liệu", "roles": ["reviewer", "admin"]},
    {"key": "feedback", "label": "Feedback Loop", "roles": ["reviewer", "admin"]},
    {"key": "users", "label": "Người dùng", "roles": ["admin"]},
    {"key": "audit", "label": "Audit Log", "roles": ["admin"]},
    {"key": "settings", "label": "Cấu hình", "roles": ["admin"]},
]

available_pages = [page for page in PAGES if can_access_page(page["roles"])]
if not available_pages:
    st.error("Tài khoản chưa được gán quyền truy cập trang nào.")
    st.stop()

if "nav_page" not in st.session_state or st.session_state["nav_page"] not in [p["key"] for p in available_pages]:
    st.session_state["nav_page"] = available_pages[0]["key"]

with st.sidebar:
    st.markdown("### Trợ Lý Cơ Khí")
    st.caption("Quản trị dữ liệu kỹ thuật & hỏi đáp RAG")
    st.markdown("---")
    st.markdown(f"**Xin chào, {user['display_name']}!**")
    st.caption(f"Phòng ban: {user.get('department')}")
    st.caption("Role: " + ", ".join(user.get("roles", [])))
    st.markdown("---")

    page_labels = {page["key"]: f"{page['label']}" for page in available_pages}
    st.radio(
        "Điều hướng",
        options=list(page_labels.keys()),
        format_func=lambda key: page_labels[key],
        key="nav_page",
        label_visibility="collapsed",
    )

    st.markdown("---")
    if st.button("Đăng xuất", use_container_width=True):
        auth.logout()

page = st.session_state["nav_page"]

if page == "dashboard":
    import app_dashboard
    app_dashboard.run_dashboard()
elif page == "chatbot":
    import app_chatbot
    app_chatbot.run_chat()
elif page == "upload":
    import app_upload
    app_upload.run_upload()
elif page == "queue":
    import app_queue
    app_queue.run_queue()
elif page == "review":
    import app_review
    app_review.run_review()
elif page == "documents":
    import app_documents
    app_documents.run_documents()
elif page == "feedback":
    import app_feedback
    app_feedback.run_feedback()
elif page == "users":
    import app_users
    app_users.run_users()
elif page == "audit":
    import app_audit
    app_audit.run_audit()
elif page == "settings":
    import app_settings
    app_settings.run_settings()
