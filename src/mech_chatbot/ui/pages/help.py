"""P2 - Trang Tro giup / Onboarding ngan gon.

Danh cho nguoi dung phong KHONG ranh ky thuat: huong dan dat cau hoi tot,
cach doc nguon trich dan, quy trinh tai tai lieu, va FAQ. Hien thi tuy theo role.
Khong phu thuoc DB -> luon hien thi duoc.
"""
import streamlit as st

from mech_chatbot.auth import service as auth


def _role_set():
    user = auth.get_current_user() or {}
    return set(user.get("roles", []))


def run_help():
    user = auth.get_current_user() or {}
    roles = _role_set()
    name = user.get("display_name") or "bạn"

    st.title("👋 Hướng dẫn sử dụng nhanh")
    st.caption("Trang trợ giúp ngắn gọn — dành cho người mới, không cần biết kỹ thuật.")

    st.success(
        f"Chào {name}! Đây là trợ lý hỏi đáp tài liệu nội bộ. "
        "Bạn đặt câu hỏi bằng tiếng Việt bình thường, hệ thống sẽ tìm trong kho tài liệu "
        "của công ty và trả lời kèm nguồn trích dẫn."
    )

    # ---- Bắt đầu nhanh ----
    st.header("1. Bắt đầu trong 30 giây")
    st.markdown(
        "- Vào trang **Chatbot hỏi đáp** ở thanh bên trái.\n"
        "- Gõ câu hỏi vào ô chat, ví dụ: *“Vật liệu của bản vẽ ABC-123 là gì?”*.\n"
        "- Đọc câu trả lời và bấm vào **nguồn trích dẫn** để xem tài liệu gốc.\n"
        "- Nếu câu trả lời chưa đúng, bấm nút phản hồi để báo cho quản trị viên."
    )

    # ---- Đặt câu hỏi tốt ----
    st.header("2. Mẹo đặt câu hỏi tốt")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Nên** ✅")
        st.markdown(
            "- Nêu rõ mã bản vẽ / mã vật tư nếu có.\n"
            "- Hỏi từng ý một, ngắn gọn.\n"
            "- Dùng từ khóa cụ thể (vật liệu, dung sai, công đoạn...)."
        )
    with col2:
        st.markdown("**Tránh** ⚠️")
        st.markdown(
            "- Câu hỏi quá chung chung (“cho tôi xem tài liệu”).\n"
            "- Gộp nhiều câu hỏi vào một dòng.\n"
            "- Viết tắt khó hiểu."
        )

    st.info(
        "💡 Nếu hệ thống trả lời *“không tìm thấy”*, hãy thử diễn đạt lại bằng từ khóa khác "
        "hoặc kểm mã tài liệu. Có thể tài liệu chưa được tải lên hoặc bạn chưa có quyền xem."
    )

    # ---- Hiểu về nguồn & quyền ----
    st.header("3. Nguồn trích dẫn & quyền xem")
    st.markdown(
        "- Mỗi câu trả lời đều kèm **nguồn** (tên tài liệu, trang) để bạn kiểm chứng.\n"
        "- Bạn chỉ thấy tài liệu thuộc **phòng ban / khu vực** và **mức mật** mà bạn được phép.\n"
        "- Nếu cần xem tài liệu ngoài quyền, liên hệ quản trị viên để cấp quyền."
    )

    # ---- Theo role ----
    if roles & {"uploader", "admin"}:
        st.header("4. Dành cho người tải tài liệu")
        st.markdown(
            "- Vào **Tải tài liệu**, chọn đúng **phòng ban/thư mục** trước khi tải.\n"
            "- Đặt tên file rõ ràng, kèm mã bản vẽ và phiên bản (ví dụ `ABC-123_v2.pdf`).\n"
            "- Sau khi tải, theo dõi tiến độ ở trang **Tiến trình ingest**.\n"
            "- Hệ thống hỗ trợ PDF, ảnh, Word, Excel, PowerPoint, CSV, và file văn bản."
        )
    if roles & {"reviewer", "admin"}:
        st.header("5. Dành cho người duyệt")
        st.markdown(
            "- Vào **Duyệt tài liệu** để kiểm tra kết quả bóc tách và phân loại của AI.\n"
            "- Sửa metadata (mã, phiên bản, loại tài liệu) nếu cần rồi bấm **Duyệt** hoặc **Từ chối**.\n"
            "- Trang **Kho tài liệu** cho phép lọc, xem và xóa tài liệu đã ingest."
        )
    if "admin" in roles:
        st.header("6. Dành cho quản trị viên")
        st.markdown(
            "- **Người dùng**: tạo tài khoản, gán role, phòng ban, khu vực.\n"
            "- **Từ điển vật tư**: khai báo mã vật liệu & từ đồng nghĩa (không cần sửa code).\n"
            "- **Audit Log**: theo dõi thao tác quan trọng.\n"
            "- **Cấu hình**: các thiết lập hệ thống."
        )

    # ---- FAQ ----
    st.header("❓ Câu hỏi thường gặp")
    with st.expander("Tại sao tôi không thấy một tài liệu?"):
        st.write("Có thể tài liệu thuộc phòng ban/khu vực khác hoặc mức mật cao hơn quyền của bạn, "
                 "hoặc chưa được duyệt. Hãy liên hệ quản trị viên.")
    with st.expander("Câu trả lời có chính xác không?"):
        st.write("Hệ thống trả lời dựa trên tài liệu nội bộ và luôn kèm nguồn. Hãy mở nguồn để "
                 "kiểm chứng trước khi sử dụng cho công việc quan trọng.")
    with st.expander("Tôi báo lỗi / góp ý ở đâu?"):
        st.write("Dùng nút phản hồi ngay dưới câu trả lời, hoặc báo trực tiếp cho quản trị viên / bộ phận IT.")

    st.markdown("---")
    st.caption("Cần hỗ trợ thêm? Liên hệ quản trị viên hệ thống hoặc bộ phận IT.")
