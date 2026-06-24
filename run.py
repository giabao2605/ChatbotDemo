"""
Entry point để chạy ứng dụng Streamlit.
Dùng: streamlit run run.py
"""
import sys
import os

# Thêm src/ vào Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Streamlit sẽ tự chạy app khi exec file này
# Import tất cả nội dung từ app chính
exec(open(os.path.join(os.path.dirname(__file__), "src", "mech_chatbot", "ui", "app.py"), encoding="utf-8").read())
