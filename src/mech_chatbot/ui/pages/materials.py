"""P2 - Trang quan tri Tu dien ma vat tu & dong nghia (chi admin).

Thay cho viec sua tay danh sach hardcode trong code. Moi thay doi co hieu luc
ngay (registry tu refresh cache) cho ca trich xuat khi ingest lan guard RAG.
"""
import streamlit as st

from mech_chatbot.auth import service as auth
from mech_chatbot.db.repository import (
    engine,
    list_materials,
    upsert_material,
    delete_material,
    add_material_synonym,
    delete_material_synonym,
)


def run_materials():
    st.title("Từ điển mã vật tư & đồng nghĩa")
    st.caption(
        "Quản trị danh mục vật liệu chuẩn + từ đồng nghĩa dùng cho trích xuất & chuẩn hóa "
        "khi ingest, và guard chống bịa vật liệu trong RAG. "
        "Chỉnh ở đây có hiệu lực ngay — không cần sửa code."
    )

    if not auth.has_role("admin"):
        st.warning("Chỉ admin mới truy cập được trang này.")
        return
    if engine is None:
        st.error("Không kết nối được Database.")
        return

    # ---- Form them moi ----
    with st.expander("➕ Thêm vật liệu mới", expanded=False):
        with st.form("add_material"):
            c1, c2, c3 = st.columns(3)
            code = c1.text_input("Mã chuẩn (vd SUS304)")
            display = c2.text_input("Tên hiển thị (vd SUS 304)")
            category = c3.text_input("Nhóm (vd stainless steel)")
            if st.form_submit_button("Thêm", type="primary"):
                if code.strip():
                    upsert_material(code, display or code, category or None, True)
                    st.success(f"Đã thêm/cập nhật '{code}'.")
                    st.rerun()
                else:
                    st.error("Phải nhập Mã chuẩn.")

    st.markdown("---")
    materials = list_materials()
    if not materials:
        st.info("Chưa có vật liệu nào. Hãy thêm ở trên hoặc chạy migration P2 để seed dữ liệu gốc.")
        return

    st.markdown(f"**Tổng cộng: {len(materials)} vật liệu**")
    for m in materials:
        status = "🟢" if m["is_active"] else "⚪"
        header = (f"{status} {m['code']} — {m['display']}  ·  "
                  f"{m['category'] or '—'}  ·  {len(m['synonyms'])} đồng nghĩa")
        with st.expander(header):
            with st.form(f"edit_{m['material_id']}"):
                e1, e2, e3, e4 = st.columns([2, 2, 2, 1])
                code = e1.text_input("Mã chuẩn", value=m["code"], key=f"c_{m['material_id']}")
                display = e2.text_input("Tên hiển thị", value=m["display"], key=f"d_{m['material_id']}")
                category = e3.text_input("Nhóm", value=m["category"] or "", key=f"cat_{m['material_id']}")
                is_active = e4.checkbox("Bật", value=m["is_active"], key=f"a_{m['material_id']}")
                b1, b2 = st.columns(2)
                if b1.form_submit_button("Lưu thay đổi", type="primary"):
                    upsert_material(code, display, category or None, is_active, material_id=m["material_id"])
                    st.success("Đã lưu.")
                    st.rerun()
                if b2.form_submit_button("Xóa vật liệu"):
                    delete_material(m["material_id"])
                    st.warning(f"Đã xóa '{m['code']}'.")
                    st.rerun()

            st.markdown("**Từ đồng nghĩa**")
            if m["synonyms"]:
                for syn in m["synonyms"]:
                    s1, s2 = st.columns([4, 1])
                    s1.write(f"• {syn['synonym']}")
                    if s2.button("Xóa", key=f"dels_{syn['synonym_id']}"):
                        delete_material_synonym(syn["synonym_id"])
                        st.rerun()
            else:
                st.caption("_Chưa có đồng nghĩa._")
            with st.form(f"addsyn_{m['material_id']}"):
                ns = st.text_input("Thêm đồng nghĩa", key=f"ns_{m['material_id']}",
                                   placeholder="vd: inox 304, ss304")
                if st.form_submit_button("Thêm đồng nghĩa"):
                    if ns.strip():
                        add_material_synonym(m["material_id"], ns)
                        st.rerun()
