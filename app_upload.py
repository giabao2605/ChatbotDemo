import os
import re
import time
import streamlit as st
import auth
from db_logic import create_ingestion_job

SUPPORTED_LEARNING_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".txt", ".md",
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff",
}


def safe_folder_name(name: str) -> str:
    name = str(name or "UNKNOWN")
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = name.replace("..", "_")
    return name[:100]


def run_upload():
    st.title("Tải tài liệu kỹ thuật")
    st.caption("Upload file vào hàng đợi ingest để worker xử lý nền.")

    current_user = auth.get_current_user()
    if not (auth.has_role("uploader") or auth.has_role("admin")):
        st.error("Bạn không có quyền tải tài liệu.")
        return

    allowed_departments = current_user.get("allowed_departments") or [current_user.get("department")]
    allowed_departments = [d for d in allowed_departments if d]

    with st.container(border=True):
        st.subheader("Thông tin upload")
        if auth.has_role("admin") and allowed_departments:
            target_department = st.selectbox("Phòng ban / thư mục dữ liệu", allowed_departments)
        else:
            target_department = current_user.get("department") or "UNKNOWN"
            st.text_input("Phòng ban / thư mục dữ liệu", value=target_department, disabled=True)

        uploaded_files = st.file_uploader(
            "Kéo thả file vào đây hoặc chọn file",
            type=sorted(ext.lstrip(".") for ext in SUPPORTED_LEARNING_EXTENSIONS),
            accept_multiple_files=True,
        )
        submitted = st.button("Đưa vào hàng đợi xử lý", type="primary", use_container_width=True, disabled=not uploaded_files)

    if submitted:
        save_uploaded_files(uploaded_files, target_department, current_user)


def save_uploaded_files(uploaded_files, target_department, current_user):
    success_count = 0
    fail_count = 0
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dept_folder = safe_folder_name(target_department)
    upload_dir = os.path.join(base_dir, "Data_Goc", dept_folder)
    os.makedirs(upload_dir, exist_ok=True)

    with st.status("Đang lưu file và tạo job ingest...", expanded=True) as status_box:
        for idx, uploaded_file in enumerate(uploaded_files):
            raw_name = os.path.basename(uploaded_file.name)
            safe_original_name = re.sub(r'[\\/*?:"<>|]', "_", raw_name)[:180]
            safe_filename = f"{int(time.time())}_{idx}_{safe_original_name}"
            file_path = os.path.join(upload_dir, safe_filename)
            try:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                job_id = create_ingestion_job(safe_original_name, file_path, dept_folder, uploaded_by=current_user["username"])
                if job_id:
                    success_count += 1
                    st.write(f"[{uploaded_file.name}] → JobID `{job_id}`")
                else:
                    fail_count += 1
                    st.write(f"[{uploaded_file.name}] → Không tạo được job")
            except Exception as e:
                fail_count += 1
                st.write(f"[{uploaded_file.name}] → Lỗi: {e}")

        if fail_count == 0:
            status_box.update(label=f"Hoàn tất: {success_count}/{len(uploaded_files)} file", state="complete")
        else:
            status_box.update(label=f"Hoàn tất nhưng có lỗi: thành công {success_count}, lỗi {fail_count}", state="error")
