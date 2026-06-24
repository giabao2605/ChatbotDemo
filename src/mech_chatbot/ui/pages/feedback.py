import streamlit as st
from sqlalchemy import text
from mech_chatbot.auth import service as auth
from mech_chatbot.db.repository import engine

FAILURE_TYPES = [
    "wrong_version", "wrong_source", "retrieval_miss", "ocr_error", "bom_parse_error",
    "hallucination", "should_refuse", "permission_error", "other",
]


def run_feedback():
    st.title("Feedback Loop")
    st.caption("Phân loại câu trả lời bị dislike để cải thiện RAG và golden set.")
    if not (auth.has_role("reviewer") or auth.has_role("admin")):
        st.error("Bạn không có quyền xử lý feedback.")
        return
    if engine is None:
        st.error("Không thể kết nối Database.")
        return

    only_pending = st.checkbox("Chỉ hiện feedback chưa xử lý", value=True)
    feedbacks = load_feedbacks(only_pending)
    if not feedbacks:
        st.info("Không có feedback cần xử lý.")
        return
    for fb in feedbacks:
        render_feedback_item(fb)


def load_feedbacks(only_pending):
    query = """
        SELECT FeedbackID, ChatID, Question, BotAnswer, FailureType,
               CorrectAnswer, AddedToGoldenSet, CreatedAt
        FROM FeedbackReview
        WHERE 1 = 1
    """
    if only_pending:
        query += " AND ISNULL(AddedToGoldenSet, 0) = 0"
    query += " ORDER BY CreatedAt DESC"
    with engine.connect() as conn:
        return conn.execute(text(query)).fetchall()


def render_feedback_item(fb):
    fid, cid, question, bot_answer, failure_type, correct_answer, added, created = fb
    title_q = (question or "")[:80]
    with st.expander(f"[{created}] ChatID {cid} · {title_q}"):
        st.write("### Câu hỏi")
        st.write(question or "")
        st.write("### Câu trả lời bot")
        st.write(bot_answer or "")
        selected_type = st.selectbox(
            "Loại lỗi", FAILURE_TYPES,
            index=FAILURE_TYPES.index(failure_type) if failure_type in FAILURE_TYPES else 0,
            key=f"type_{fid}",
        )
        correct_ans = st.text_area("Câu trả lời đúng", value=correct_answer or "", key=f"correct_{fid}")
        reviewer_note = st.text_area("Ghi chú reviewer", key=f"note_{fid}")
        if st.button("Lưu phân loại", type="primary", key=f"save_{fid}"):
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE FeedbackReview
                    SET FailureType = :ft,
                        CorrectAnswer = :ca,
                        ReviewerNote = :note,
                        AddedToGoldenSet = 1
                    WHERE FeedbackID = :fid
                """), {"ft": selected_type, "ca": correct_ans, "note": reviewer_note, "fid": fid})
            st.success("Đã cập nhật feedback.")
            st.rerun()
