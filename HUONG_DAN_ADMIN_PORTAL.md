# Hướng dẫn dùng bản giao diện admin đã tách trang

## 1. Chạy ứng dụng

Cách Docker:

```bash
docker-compose up -d --build
```

Cách local development:

```bash
pip install -r requirements-core.txt
python rag_server.py
python scripts/ingestion_worker.py
streamlit run app.py
```

## 2. Menu theo role

- `viewer`: Chatbot hỏi đáp.
- `uploader`: Chatbot hỏi đáp, Tải tài liệu, Tiến trình ingest.
- `reviewer`: Chatbot hỏi đáp, Duyệt tài liệu, Kho tài liệu, Feedback Loop.
- `admin`: Toàn bộ trang: Tổng quan, Chatbot, Upload, Queue, Review, Documents, Feedback, Users, Audit, Settings.

## 3. Luồng dùng khuyến nghị

### Admin

1. Vào **Tổng quan** để xem số tài liệu, job lỗi, feedback cần xử lý.
2. Vào **Người dùng** để tạo/gán role cho tài khoản.
3. Vào **Audit Log** để xem lịch sử thao tác.
4. Vào **Cấu hình** để kiểm tra trạng thái RAG/API/DB.

### Uploader

1. Vào **Tải tài liệu**.
2. Chọn phòng ban/thư mục dữ liệu.
3. Upload PDF/DOCX/XLSX/ảnh/txt/csv.
4. Bấm **Đưa vào hàng đợi xử lý**.
5. Qua **Tiến trình ingest** để xem worker xử lý tới đâu.

### Reviewer

1. Vào **Duyệt tài liệu**.
2. Kiểm tra AI Classification và metadata.
3. Chọn publish làm version mới / variant mới / standalone / từ chối.
4. Vào **Feedback Loop** để phân loại câu trả lời bị dislike.

### Viewer

1. Vào **Chatbot hỏi đáp**.
2. Hỏi tài liệu kỹ thuật đã được duyệt.
3. Có thể upload ảnh để hỏi/phân tích, nhưng không upload tài liệu vào hệ thống.

## 4. Migration khuyến nghị cho multi-user chat history

Nếu nhiều user dùng chung app, nên chạy file:

```text
database/migrations/2026_06_24_add_chat_username.sql
```

Migration này thêm cột `Username` cho `LichSuChat` để sau này lọc lịch sử chat theo từng user.

## 5. Ghi chú thay đổi chính

- `app.py` đã thành router theo role.
- Thêm `app_dashboard.py`, `app_upload.py`, `app_documents.py`, `app_feedback.py`, `app_users.py`, `app_audit.py`, `app_settings.py`.
- Chatbot chỉ nhận ảnh; upload tài liệu đã chuyển sang trang **Tải tài liệu**.
- `app_queue.py` có filter status/search và progress bar.
- CSS dùng chung nằm trong `ui_theme.py`.
