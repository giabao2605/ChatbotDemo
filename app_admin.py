import streamlit as st
from sqlalchemy import text
from db_logic import engine
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()
qdrant_url = os.getenv("QDRANT_URL", "")
qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
qdrant_path = os.getenv("QDRANT_PATH", "Mechanical_Qdrant_DB")

def update_qdrant_status(ten_file, thu_muc, new_status):
    try:
        if qdrant_url:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            client = QdrantClient(path=qdrant_path)
        collection_name = "TaiLieuKyThuat_v2"
        from qdrant_client.http import models
        
        # Find all points with this file_goc AND thu_muc
        points, _ = client.scroll(
            collection_name=collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.file_goc",
                        match=models.MatchValue(value=ten_file)
                    ),
                    models.FieldCondition(
                        key="metadata.phong_ban_quyen",
                        match=models.MatchValue(value=thu_muc)
                    )
                ]
            ),
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
        
        for p in points:
            new_metadata = p.payload.get("metadata", {})
            new_metadata["doc_status"] = new_status
            client.set_payload(
                collection_name=collection_name,
                payload={"metadata": new_metadata},
                points=[p.id],
            )
        return True
    except Exception as e:
        st.error(f"Lỗi cập nhật Qdrant: {e}")
        return False

def run_admin():
    st.title("Duyệt Tài Liệu Đầu Vào")
    st.markdown("Xem danh sách các tài liệu AI vừa bóc tách xong. Quyết định duyệt (đưa vào sử dụng) hoặc từ chối.")

    if engine is None:
        st.error("Không thể kết nối đến Database.")
        return

    # Filter tab
    tabs = st.tabs(["Chờ Duyệt (Pending)", "Đã Duyệt (Published)", "Bị Từ Chối (Rejected)"])
    
    with engine.connect() as conn:
        # Lay danh sach tai lieu
        query = text("""
            SELECT t.DocID, t.TenFile, t.ThuMuc, t.TrangThai, t.NgayTaiLen,
                   tk.MaDoiTuong, tk.LoaiTaiLieu, tk.TenSanPham, tk.VatLieu, tk.DungSaiDay, tk.KichThuocTongThe
            FROM TaiLieu t
            LEFT JOIN TaiLieuKyThuat tk ON t.DocID = tk.DocID AND tk.TrangSo = 1
            ORDER BY t.NgayTaiLen DESC
        """)
        result = conn.execute(query)
        all_docs = result.fetchall()

    pending_docs = [d for d in all_docs if d[3] == "pending_review"]
    published_docs = [d for d in all_docs if d[3] == "published"]
    rejected_docs = [d for d in all_docs if d[3] == "rejected"]

    def render_doc_list(docs, show_actions=False):
        if not docs:
            st.info("Không có tài liệu nào trong danh sách này.")
            return

        for d in docs:
            doc_id, ten_file, thu_muc, trang_thai, ngay_tai_len, ma_dt, loai_tl, ten_sp, vat_lieu, dung_sai, kich_thuoc = d
            with st.expander(f"{ten_file} - Tải lên: {ngay_tai_len.strftime('%Y-%m-%d')}"):
                st.write(f"**Thư mục:** {thu_muc}")
                st.markdown("### AI Bóc Tách Metadata:")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"- **Mã đối tượng:** `{ma_dt}`")
                    st.write(f"- **Loại:** {loai_tl}")
                    st.write(f"- **Tên SP:** {ten_sp}")
                with col2:
                    st.write(f"- **Vật liệu:** {vat_lieu}")
                    st.write(f"- **Kích thước:** {kich_thuoc}")
                    st.write(f"- **Dung sai:** {dung_sai}")

                if show_actions:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Duyệt & Publish", key=f"pub_{doc_id}", type="primary"):
                            with engine.begin() as conn_w:
                                conn_w.execute(text("UPDATE TaiLieu SET TrangThai = 'published', NgayDuyet = GETDATE() WHERE DocID = :id"), {"id": doc_id})
                            if update_qdrant_status(ten_file, thu_muc, "published"):
                                st.success("Đã duyệt thành công!")
                                st.rerun()
                    with col_b:
                        if st.button("Từ Chối", key=f"rej_{doc_id}"):
                            with engine.begin() as conn_w:
                                conn_w.execute(text("UPDATE TaiLieu SET TrangThai = 'rejected', NgayDuyet = GETDATE() WHERE DocID = :id"), {"id": doc_id})
                            if update_qdrant_status(ten_file, thu_muc, "rejected"):
                                st.warning("Đã từ chối tài liệu.")
                                st.rerun()

    with tabs[0]:
        render_doc_list(pending_docs, show_actions=True)
    with tabs[1]:
        render_doc_list(published_docs, show_actions=False)
    with tabs[2]:
        render_doc_list(rejected_docs, show_actions=False)
