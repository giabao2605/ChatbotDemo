"""Cau hinh dung chung — tach khoi cac module de ho tro da phong ban.

QDRANT_COLLECTION: ten collection vector store dung CHUNG cho moi phong ban.
- Day chi la dinh danh NOI BO (nguoi dung khong nhin thay tren UI).
- Khong gan voi 'co khi' — moi phong ban deu luu chung o day, phan biet bang
  payload (domain / security_level / phong_ban) chu khong phai bang ten collection.
- Mac dinh giu ten cu 'TaiLieuKyThuat_v2' de KHONG lam mat du lieu da nap.
- Muon doi sang ten trung tinh (vd 'KnowledgeBase_v2'): dat bien moi truong
  QDRANT_COLLECTION trong .env, roi chay scripts/migrate_qdrant_collection.py
  de di tru toan bo vector sang ten moi (Qdrant khong ho tro rename truc tiep).
"""
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "TaiLieuKyThuat_v2")
