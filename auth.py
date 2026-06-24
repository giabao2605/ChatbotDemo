from pathlib import Path

import bcrypt
import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import text
from db_logic import engine

def authenticate_user(username, password):
    if engine is None:
        return None
    try:
        with engine.connect() as conn:
            user = conn.execute(
                text(
                    """
                    SELECT UserID, Username, DisplayName, Department, IsActive, PasswordHash
                    FROM Users
                    WHERE Username = :u
                    """
                ),
                {"u": username},
            ).fetchone()
            
            if not user:
                return None
            if not user[4]:
                return None
                
            stored_hash = user[5]
            
            # Verify bcrypt hash
            try:
                if stored_hash is None:
                    is_valid = False
                else:
                    is_valid = bcrypt.checkpw(
                        password.encode("utf-8"),
                        stored_hash.encode("utf-8"),
                    )
            except Exception:
                is_valid = False
                
            if not is_valid:
                return None
                
            roles = conn.execute(
                text(
                    """
                    SELECT r.RoleName
                    FROM Roles r
                    JOIN UserRoles ur ON r.RoleID = ur.RoleID
                    WHERE ur.UserID = :uid
                    """
                ),
                {"uid": user[0]},
            ).fetchall()
            
            role_list = [r[0] for r in roles]
            
            try:
                dept_rows = conn.execute(
                    text("SELECT Department FROM UserDepartments WHERE UserID = :uid"),
                    {"uid": user[0]}
                ).fetchall()
                allowed_departments = [r[0] for r in dept_rows]
            except Exception:
                allowed_departments = []
                
            if user[3] and user[3] not in allowed_departments:
                allowed_departments.append(user[3])
            
            return {
                "user_id": user[0],
                "username": user[1],
                "display_name": user[2],
                "department": user[3],
                "roles": role_list,
                "allowed_departments": allowed_departments,
            }
    except Exception as e:
        st.error(f"Lỗi truy vấn: {e}")
        return None

_LIQUID_LOGIN_COMPONENT = components.declare_component(
    "liquid_login",
    path=str(Path(__file__).parent / "components" / "liquid_login"),
)


def _inject_login_page_css():
    """Chỉ reset layout Streamlit; hiệu ứng login nằm nguyên trong custom component."""
    st.markdown(
        """
        <style>
        /* Giữ nền mặc định của Streamlit, chỉ reset layout cho trang login */
        [data-testid="stAppViewContainer"] .block-container {
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        [data-testid="stVerticalBlock"],
        [data-testid="element-container"],
        .stCustomComponentV1 {
            height: 100vh !important;
            min-height: 100vh !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        iframe {
            display: block !important;
            width: 100vw !important;
            height: 100vh !important;
            min-height: 100vh !important;
            border: none !important;
            background: transparent !important;
        }
        header[data-testid="stHeader"] { background: transparent; }
        #MainMenu, footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def login_screen():
    _inject_login_page_css()

    error_message = st.session_state.pop("login_error", "")
    result = _LIQUID_LOGIN_COMPONENT(error=error_message, default=None, key="liquid_login")

    if result and result.get("submittedAt"):
        username = (result.get("username") or "").strip()
        password = result.get("password") or ""
        user_data = authenticate_user(username, password)
        if user_data:
            st.session_state["user"] = user_data
            st.rerun()

        st.session_state["login_error"] = "Sai tên đăng nhập hoặc mật khẩu, hoặc tài khoản bị khóa."
        st.rerun()

    return False

def check_auth():
    if "user" not in st.session_state:
        logged_in = login_screen()
        if not logged_in:
            st.stop()

def get_current_user():
    return st.session_state.get("user")

def has_role(role_name):
    user = get_current_user()
    if not user:
        return False
    return role_name in user["roles"] or "admin" in user["roles"]

def logout():
    if "user" in st.session_state:
        del st.session_state["user"]
    st.rerun()



def is_admin():
    return has_role("admin")


def get_allowed_departments():
    user = get_current_user()
    if not user:
        return []
    allowed = list(user.get("allowed_departments") or [])
    dept = user.get("department")
    if dept and dept not in allowed:
        allowed.append(dept)
    return allowed
