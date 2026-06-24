import streamlit as st
from sqlalchemy import text
import auth
from db_logic import engine, update_document_full_metadata, delete_document_completely


def run_documents():
    st.title("Kho tài liệu")
    st.caption("Tra cứu, lọc và quản lý tài liệu đã ingest.")

    if not (auth.has_role("reviewer") or auth.has_role("admin")):
        st.error("Bạn không có quyền xem kho tài liệu.")
        return
    if engine is None:
        st.error("Không thể kết nối Database.")
        return

    current_user = auth.get_current_user()
    search = st.text_input("Tìm kiếm", placeholder="Tên file, Base Code, mã đối tượng...")
    status_filter = st.selectbox("Trạng thái", ["Tất cả", "published", "draft", "rejected", "archived", "superseded"])
    docs = load_documents(current_user, search, status_filter)

    if not docs:
        st.info("Không tìm thấy tài liệu.")
        return

    st.write(f"Tìm thấy **{len(docs)}** tài liệu.")
    for doc in docs:
        render_document_item(doc, current_user)


def load_documents(current_user, search, status_filter):
    is_admin = auth.has_role("admin")
    query = """
        SELECT TOP 200
            t.DocID, t.TenFile, t.ThuMuc, t.BaseCode, t.VersionNo, t.VersionLabel,
            t.VariantCode, t.VariantGroup, t.LifecycleStatus, t.ReviewStatus,
            t.IsCurrent, t.NgayTaiLen,
            tk.MaDoiTuong, tk.LoaiTaiLieu, tk.TenSanPham
        FROM TaiLieu t
        LEFT JOIN TaiLieuKyThuat tk ON t.DocID = tk.DocID AND tk.TrangSo = 1
        WHERE 1 = 1
    """
    params = {}
    if status_filter != "Tất cả":
        query += " AND t.LifecycleStatus = :status"
        params["status"] = status_filter
    if search:
        query += """
            AND (t.TenFile LIKE :search OR t.BaseCode LIKE :search
                 OR tk.MaDoiTuong LIKE :search OR tk.TenSanPham LIKE :search)
        """
        params["search"] = f"%{search}%"
    if not is_admin:
        allowed = current_user.get("allowed_departments") or [current_user.get("department")]
        allowed = [d for d in allowed if d]
        if allowed:
            keys = []
            for i, dept in enumerate(allowed):
                key = f"dept_{i}"
                params[key] = dept
                keys.append(f":{key}")
            query += f" AND t.ThuMuc IN ({', '.join(keys)})"
    query += " ORDER BY t.NgayTaiLen DESC"
    with engine.connect() as conn:
        return conn.execute(text(query), params).fetchall()


def render_document_item(doc, current_user):
    (doc_id, ten_file, thu_muc, base_code, version_no, version_label, variant_code,
     variant_group, lifecycle_status, review_status, is_current, ngay_tai_len,
     ma_doi_tuong, loai_tai_lieu, ten_san_pham) = doc

    current_badge = " · current" if is_current else ""
    with st.expander(f"{ten_file} · {lifecycle_status}{current_badge}"):
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**DocID:** {doc_id}")
            st.write(f"**Phòng ban:** {thu_muc}")
            st.write(f"**Base Code:** `{base_code}`")
            st.write(f"**Version:** {version_no} - {version_label}")
            st.write(f"**Variant:** {variant_code}")
        with c2:
            st.write(f"**Review:** {review_status}")
            st.write(f"**Lifecycle:** {lifecycle_status}")
            st.write(f"**Ngày tải:** {ngay_tai_len}")
            st.write(f"**Mã đối tượng:** {ma_doi_tuong}")
            st.write(f"**Tên sản phẩm:** {ten_san_pham}")

        if auth.has_role("admin"):
            render_admin_actions(doc_id, base_code, version_no, version_label, variant_code, variant_group, loai_tai_lieu, current_user)


def render_admin_actions(doc_id, base_code, version_no, version_label, variant_code, variant_group, loai_tai_lieu, current_user):
    st.markdown("---")
    st.subheader("Quản trị tài liệu")
    with st.form(f"edit_doc_{doc_id}"):
        c1, c2 = st.columns(2)
        with c1:
            new_base_code = st.text_input("Base Code", value=base_code or "")
            new_version_no = st.number_input("Version No", value=int(version_no) if version_no else 1, step=1)
            new_version_label = st.text_input("Version Label", value=version_label or "")
        with c2:
            new_variant_code = st.text_input("Variant Code", value=variant_code or "default")
            new_variant_group = st.text_input("Variant Group", value=variant_group or "")
            new_doc_type = st.text_input("Document Type", value=loai_tai_lieu or "")
        submitted = st.form_submit_button("Lưu metadata", type="primary")
    if submitted:
        try:
            ok = update_document_full_metadata(
                doc_id, base_code=new_base_code, version_no=new_version_no,
                version_label=new_version_label, variant_code=new_variant_code,
                variant_group=new_variant_group, loai_tai_lieu=new_doc_type,
                reviewer=current_user["username"],
            )
            if ok:
                st.success("Đã cập nhật metadata.")
                st.rerun()
            else:
                st.error("Cập nhật thất bại.")
        except Exception as e:
            st.error(f"Lỗi cập nhật: {e}")

    confirm = st.checkbox("Tôi hiểu thao tác này sẽ xóa vĩnh viễn dữ liệu SQL + Qdrant.", key=f"confirm_delete_{doc_id}")
    if st.button("Xóa tài liệu", key=f"delete_doc_{doc_id}", disabled=not confirm, type="secondary"):
        try:
            ok = delete_document_completely(doc_id, reviewer=current_user["username"])
            if ok:
                st.success("Đã xóa tài liệu.")
                st.rerun()
            else:
                st.error("Xóa thất bại.")
        except Exception as e:
            st.error(f"Lỗi xóa: {e}")
