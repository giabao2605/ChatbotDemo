from db_logic import engine
from rag_logic import client
from sqlalchemy import text

# Kiểm tra SQL
with engine.connect() as conn:
    sql_count = conn.execute(text("SELECT COUNT(*) FROM TaiLieu")).scalar()
    print(f"SQL: {sql_count} files")

# Kiểm tra Qdrant
info = client.get_collection("TaiLieuKyThuat_v2")
print(f"Qdrant vectors: {info.points_count}")
print(f"Trung binh chunks/file: {info.points_count / max(1, sql_count):.1f}")
