import logging
from logging.handlers import RotatingFileHandler
import os

# Đảm bảo thư mục logs tồn tại
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, 'chatbot_system.log')

# Tạo logger
logger = logging.getLogger("MechChatbot")
logger.setLevel(logging.INFO)

# Tránh việc add handler nhiều lần nếu module được import nhiều nơi
if not logger.handlers:
    # Handler 1: Ghi ra file với Rotating (tối đa 5 file, mỗi file 10MB)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Handler 2: Ghi ra Console (Stream)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
