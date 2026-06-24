import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mech_chatbot.db.repository import get_pending_job

job = get_pending_job("debug-worker")
print("JOB =", job)