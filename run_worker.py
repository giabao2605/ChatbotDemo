import sys
import os

# Thêm src/ vào Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Chạy Ingestion Worker
if __name__ == "__main__":
    from mech_chatbot.workers.ingestion_worker import run_worker
    run_worker()
