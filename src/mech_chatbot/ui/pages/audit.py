import json
import streamlit as st
from sqlalchemy import text
from mech_chatbot.auth import service as auth
from mech_chatbot.db.repository import engine


def run_audit():
    st.title("Audit Log")
    if not auth.has_role("admin"):
        st.error("Chỉ admin được xem audit log.")
        return
    if engine is None:
        st.error("Không thể kết nối Database.")
        return

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        action_filter = st.text_input("Lọc action", placeholder="upload, chat_query, edit_metadata...")
    with c2:
        username_filter = st.text_input("Lọc username")
    with c3:
        # GD5 muc 3: loc nhanh cac luot doc tai lieu mat (action read_confidential).
        only_confidential = st.checkbox("🔒 Chỉ đọc tài liệu mật", help="Chỉ hiển thị các lượt truy cập tài liệu confidential (action read_confidential).")

    query = """
        SELECT TOP 300 AuditID, Username, Action, EntityType, EntityID, Details, CreatedAt
        FROM AuditLog
        WHERE 1 = 1
    """
    params = {}
    if only_confidential:
        query += " AND Action = :action"
        params["action"] = "read_confidential"
    elif action_filter:
        query += " AND Action LIKE :action"
        params["action"] = f"%{action_filter}%"
    if username_filter:
        query += " AND Username LIKE :username"
        params["username"] = f"%{username_filter}%"
    query += " ORDER BY CreatedAt DESC"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()
    if not rows:
        st.info("Không có audit log.")
        return
    for audit_id, username, action, entity_type, entity_id, details, created_at in rows:
        with st.expander(f"{created_at} · {username} · {action}"):
            st.write(f"**AuditID:** {audit_id}")
            st.write(f"**Entity:** {entity_type} #{entity_id}")
            if details:
                try:
                    st.json(json.loads(details))
                except Exception:
                    st.text(details)
