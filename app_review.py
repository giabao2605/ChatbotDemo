# Trang duyệt tài liệu.
# Để tránh thay đổi logic publish phức tạp, trang này tái sử dụng workflow duyệt hiện có trong app_admin.py.
# Các phần quản trị khác đã được tách sang app_documents.py và app_feedback.py.
import streamlit as st
import auth


def run_review():
    if not (auth.has_role("reviewer") or auth.has_role("admin")):
        st.error("Bạn không có quyền duyệt tài liệu.")
        return
    import app_admin
    app_admin.run_admin()
