"""P1-7: Trang Vong doi tai lieu (het han / nhac review) - reviewer + admin."""
import datetime
import streamlit as st
from mech_chatbot.auth import service as auth
from mech_chatbot.db.repository import (
    engine,
    get_lifecycle_overview,
    set_document_lifecycle,
    mark_document_reviewed,
    refresh_expired_status,
)
from mech_chatbot.ui.i18n import t


def _pd(s):
    if not s:
        return None
    try:
        return datetime.datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _row(item):
    did = item["doc_id"]
    st.write("**" + str(item.get("file") or ("DocID " + str(did))) + "** · v" +
             str(item.get("version_no") or "?") + " · " + str(item.get("dept") or ""))
    cap = []
    if item.get("effective_status"):
        cap.append(t("trang thai:") + " " + str(item["effective_status"]))
    if item.get("expiry_date"):
        cap.append(t("het han:") + " " + str(item["expiry_date"]))
    if item.get("review_date"):
        cap.append(t("han review:") + " " + str(item["review_date"]))
    if item.get("last_reviewed_at"):
        cap.append(t("review gan nhat:") + " " + str(item["last_reviewed_at"])[:10])
    if cap:
        st.caption(" | ".join(cap))
    c1, c2, c3 = st.columns(3)
    with c1:
        eff = st.date_input(t("Ngay hieu luc"), value=_pd(item.get("effective_date")), key="eff_" + str(did))
    with c2:
        exp = st.date_input(t("Ngay het hieu luc"), value=_pd(item.get("expiry_date")), key="exp_" + str(did))
    with c3:
        rev = st.date_input(t("Han review ke tiep"), value=_pd(item.get("review_date")), key="rev_" + str(did))
    b1, b2 = st.columns(2)
    with b1:
        if st.button(t("Luu ngay"), key="savedate_" + str(did), use_container_width=True):
            set_document_lifecycle(
                did,
                effective_date=(eff.isoformat() if eff else None),
                expiry_date=(exp.isoformat() if exp else None),
                review_date=(rev.isoformat() if rev else None),
                reviewer=(st.session_state.get("username") or "reviewer"),
            )
            st.success(t("Da luu ngay vong doi."))
            st.rerun()
    with b2:
        if st.button(t("Danh dau da review (+180 ngay)"), key="review_" + str(did), use_container_width=True):
            mark_document_reviewed(did, reviewer=(st.session_state.get("username") or "reviewer"), next_review_days=180)
            st.success(t("Da ghi nhan review."))
            st.rerun()
    st.divider()


def run_lifecycle():
    st.title("🗓️ " + t("Vong doi tai lieu (het han / nhac review)"))
    if not (auth.has_role("reviewer") or auth.has_role("admin")):
        st.error(t("Ban khong co quyen truy cap trang nay."))
        return
    if engine is None:
        st.error(t("Khong ket noi duoc Database."))
        return

    cc1, cc2 = st.columns([1, 3])
    with cc1:
        if st.button(t("Cap nhat trang thai het han"), key="refresh_expired"):
            n = refresh_expired_status()
            st.success(t("Da danh dau expired cho N tai lieu.").replace("N", str(n)))
    with cc2:
        soon = st.selectbox(t("Nguong sap het han (ngay)"), [7, 15, 30, 60, 90], index=2, key="lc_soon")

    data = get_lifecycle_overview(soon_days=int(soon))
    counts = data.get("counts", {})
    m1, m2, m3 = st.columns(3)
    m1.metric(t("Da het han"), counts.get("expired", 0))
    m2.metric(t("Sap het han"), counts.get("expiring_soon", 0))
    m3.metric(t("Can review"), counts.get("needs_review", 0))

    st.subheader("⛔ " + t("Da het hieu luc"))
    exp = data.get("expired") or []
    if not exp:
        st.caption(t("Khong co."))
    for it in exp:
        _row(it)

    st.subheader("⚠️ " + t("Sap het han"))
    es = data.get("expiring_soon") or []
    if not es:
        st.caption(t("Khong co."))
    for it in es:
        _row(it)

    st.subheader("🔔 " + t("Can review"))
    nr = data.get("needs_review") or []
    if not nr:
        st.caption(t("Khong co."))
    for it in nr:
        _row(it)
