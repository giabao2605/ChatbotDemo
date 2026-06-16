import os
import time
from sqlalchemy import text
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Load .env de doc QDRANT_URL / QDRANT_PATH giong het rag_logic.py
load_dotenv()

# ====================================================
# 1. XOA DATABASE TRUOC KHI LOAD MODULES RAG
# ====================================================
print("1. Dang xoa collection Qdrant 'TaiLieuKyThuat_v2'...")
temp_client = None
try:
    qdrant_url = os.getenv("QDRANT_URL", "")
    qdrant_path = os.getenv("QDRANT_PATH", "./Mechanical_Qdrant_DB")
    if qdrant_url:
        print(f" -> Ket noi Qdrant Server: {qdrant_url}")
        temp_client = QdrantClient(url=qdrant_url)
    else:
        print(f" -> Dung Qdrant Local: {qdrant_path}")
        temp_client = QdrantClient(path=qdrant_path)
    temp_client.delete_collection(collection_name="TaiLieuKyThuat_v2")
    print(" -> Da xoa Qdrant collection thanh cong.")
except Exception as e:
    print(f" -> Khong the xoa Qdrant (co the chua ton tai): {e}")
finally:
    # Fix: dong client trong finally de giai phong file-lock o che do Qdrant local.
    # Neu khong, lan import rag_logic ngay sau co the bao 'already accessed by another instance'.
    if temp_client is not None:
        try:
            temp_client.close()
        except Exception:
            pass
    # Chờ file-lock được giải phóng hoàn toàn trên Windows trước khi import rag_logic
    time.sleep(1)

print("2. Dang import module va xoa SQL Data...")
from db_logic import engine
from file_learning import learn_new_file

print("2. Dang xoa du lieu SQL Server (TaiLieu, TaiLieuKyThuat)...")
try:
    if engine is None:
        raise RuntimeError("SQLAlchemy Engine chua khoi tao duoc (kiem tra db_logic / ODBC).")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM TaiLieuKyThuat"))
        conn.execute(text("DELETE FROM TaiLieu"))
    print(" -> Da don dep SQL Server thanh cong.")
except Exception as e:
    print(f" -> Loi xoa SQL Server: {e}")


# ====================================================
# 3. CHAY LAI INGESTION VOI PIPELINE MOI
# ====================================================
def reingest_all():
    print("\n3. Bat dau Re-ingest toan bo tu thu muc Data_Goc...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_goc_path = os.path.join(base_dir, "Data_Goc")

    if not os.path.exists(data_goc_path):
        print(f"Khong tim thay thu muc: {data_goc_path}")
        return

    success_count = 0
    fail_count = 0
    start_time = time.time()

    for root, dirs, files in os.walk(data_goc_path):
        if root == data_goc_path:
            thu_muc_name = ""
        else:
            thu_muc_name = os.path.basename(root)
        for file in files:
            # Bo qua cac file an
            if file.startswith('.'):
                continue

            file_path = os.path.join(root, file)
            print(f"\n--- Dang nap: {file} (Thu muc: {thu_muc_name}) ---")
            try:
                # Dung lai ham learn_new_file de tan dung toan bo luong xu ly chuan
                success, msg = learn_new_file(file_path, file, thu_muc=thu_muc_name)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    print(f" [!] Loi: {msg}")
            except Exception as e:
                fail_count += 1
                print(f" [!] Exception: {e}")

    total_time = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"HOAN TAT RE-INGEST: Thanh cong {success_count} file, That bai {fail_count} file")
    print(f"Tong thoi gian: {total_time:.2f} giay (Trung binh: {total_time/max(1, success_count):.2f}s/file)")
    print("=" * 50)


if __name__ == "__main__":
    print("\n" + "!" * 50)
    print("CANH BAO: TOOL SE XOA TOAN BO DU LIEU RAG VA NAP LAI TU DAU.")
    confirm = input("Ban co chac chan muon tiep tuc? (y/n): ")
    if confirm.lower() == 'y':
        reingest_all()
    else:
        print("Da huy thao tac.")