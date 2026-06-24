import bcrypt
import streamlit as st
from sqlalchemy import text
from mech_chatbot.auth import service as auth
from mech_chatbot.db.repository import engine

ROLE_OPTIONS = ["admin", "reviewer", "uploader", "viewer"]


def run_users():
    st.title("Quản lý người dùng")
    if not auth.has_role("admin"):
        st.error("Chỉ admin được truy cập trang này.")
        return
    if engine is None:
        st.error("Không thể kết nối Database.")
        return
    tab_list, tab_create = st.tabs(["Danh sách người dùng", "Tạo người dùng"])
    with tab_list:
        render_user_list()
    with tab_create:
        render_create_user()


def render_user_list():
    with engine.connect() as conn:
        users = conn.execute(text("""
            SELECT UserID, Username, DisplayName, Department, IsActive, CreatedAt
            FROM Users
            ORDER BY CreatedAt DESC
        """)).fetchall()
    for user_id, username, display_name, department, is_active, created_at in users:
        with st.expander(f"{username} · {display_name or ''}"):
            st.write(f"**UserID:** {user_id}")
            st.write(f"**Department:** {department}")
            st.write(f"**Created:** {created_at}")
            st.write("**Roles:** " + ", ".join(get_user_roles(user_id)))
            st.write("**Allowed departments:** " + ", ".join(get_user_departments(user_id)))
            new_active = st.checkbox("Active", value=bool(is_active), key=f"active_{user_id}")
            if st.button("Lưu trạng thái", key=f"save_active_{user_id}"):
                with engine.begin() as conn:
                    conn.execute(text("UPDATE Users SET IsActive = :active WHERE UserID = :uid"), {"active": 1 if new_active else 0, "uid": user_id})
                st.success("Đã cập nhật.")
                st.rerun()


def render_create_user():
    username = st.text_input("Username")
    display_name = st.text_input("Tên hiển thị")
    department = st.text_input("Phòng ban")
    password = st.text_input("Mật khẩu", type="password")
    selected_roles = st.multiselect("Roles", ROLE_OPTIONS, default=["viewer"])
    allowed_departments_text = st.text_input("Allowed departments", placeholder="Ví dụ: Ky_Thuat, Tu_Hoc")

    if st.button("Tạo user", type="primary"):
        if not username or not password:
            st.error("Username và mật khẩu là bắt buộc.")
            return
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        allowed_departments = [d.strip() for d in allowed_departments_text.split(",") if d.strip()]
        if department and department not in allowed_departments:
            allowed_departments.append(department)
        try:
            with engine.begin() as conn:
                row = conn.execute(text("""
                    INSERT INTO Users (Username, PasswordHash, DisplayName, Department, IsActive)
                    OUTPUT INSERTED.UserID
                    VALUES (:u, :p, :d, :dept, 1)
                """), {"u": username, "p": password_hash, "d": display_name, "dept": department}).fetchone()
                user_id = row[0]
                for role in selected_roles:
                    conn.execute(text("""
                        INSERT INTO UserRoles (UserID, RoleID)
                        SELECT :uid, RoleID FROM Roles WHERE RoleName = :role
                    """), {"uid": user_id, "role": role})
                for dept in allowed_departments:
                    conn.execute(text("INSERT INTO UserDepartments (UserID, Department) VALUES (:uid, :dept)"), {"uid": user_id, "dept": dept})
            st.success("Đã tạo người dùng.")
            st.rerun()
        except Exception as e:
            st.error(f"Không tạo được user: {e}")


def get_user_roles(user_id):
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT r.RoleName FROM Roles r JOIN UserRoles ur ON r.RoleID = ur.RoleID WHERE ur.UserID = :uid
        """), {"uid": user_id}).fetchall()
    return [r[0] for r in rows]


def get_user_departments(user_id):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT Department FROM UserDepartments WHERE UserID = :uid"), {"uid": user_id}).fetchall()
    return [r[0] for r in rows]
