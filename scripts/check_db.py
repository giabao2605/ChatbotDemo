import os
import sys
from sqlalchemy import text
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_logic import engine

if engine:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT MaDoiTuong, CongDoan, YCKT FROM TaiLieuKyThuat WHERE MaDoiTuong LIKE '%8.3.05571%'")).fetchall()
        for r in res:
            print(f"Ma: {r[0]}, CongDoan: {r[1]}")
            # print(f"NoiDung: {r[2][:100]}...")
