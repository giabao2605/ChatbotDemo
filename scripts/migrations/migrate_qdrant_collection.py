"""Di tru toan bo vector tu collection CU sang collection MOI (doi ten an toan).

Qdrant KHONG ho tro rename collection truc tiep, nen script nay:
  1. Doc cau hinh vector tu collection NGUON.
  2. Tao collection DICH (neu chua co) voi cung cau hinh.
  3. Scroll toan bo diem (payload + vector) tu NGUON -> upsert sang DICH theo lo.

Cach dung:
  # B1: dat ten moi trong .env ->  QDRANT_COLLECTION=KnowledgeBase_v2
  # B2: chay di tru tu ten cu sang ten moi (lay tu env):
  python scripts/migrations/migrate_qdrant_collection.py --source TaiLieuKyThuat_v2
  # B3: tao lai payload index cho collection moi:
  python scripts/create_qdrant_indexes.py

Tham so:
  --source   : ten collection cu (mac dinh: TaiLieuKyThuat_v2)
  --target   : ten collection moi (mac dinh: lay tu env QDRANT_COLLECTION)
  --batch    : so diem moi lo (mac dinh 256)
  --recreate : xoa collection DICH neu da ton tai roi tao lai
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="TaiLieuKyThuat_v2")
    parser.add_argument("--target", default=os.getenv("QDRANT_COLLECTION", "TaiLieuKyThuat_v2"))
    parser.add_argument("--batch", type=int, default=256)
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args()

    if args.source == args.target:
        print(f"[!] Nguon va dich trung ten ('{args.source}'). Khong can di tru.")
        sys.exit(0)

    client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=300)

    if not client.collection_exists(args.source):
        print(f"[X] Collection nguon '{args.source}' khong ton tai.")
        sys.exit(1)

    src_info = client.get_collection(args.source)
    vectors_config = src_info.config.params.vectors
    sparse_config = src_info.config.params.sparse_vectors

    if args.recreate and client.collection_exists(args.target):
        print(f"[*] Xoa collection dich cu '{args.target}'...")
        client.delete_collection(args.target)

    if not client.collection_exists(args.target):
        print(f"[*] Tao collection dich '{args.target}'...")
        client.create_collection(
            collection_name=args.target,
            vectors_config=vectors_config,
            sparse_vectors_config=sparse_config,
        )

    print(f"[*] Bat dau di tru '{args.source}' -> '{args.target}' (batch={args.batch})...")
    offset = None
    total = 0
    while True:
        points, offset = client.scroll(
            collection_name=args.source,
            limit=args.batch,
            with_payload=True,
            with_vectors=True,
            offset=offset,
        )
        if not points:
            break
        client.upsert(
            collection_name=args.target,
            points=[models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points],
        )
        total += len(points)
        print(f"    da chep {total} diem...")
        if offset is None:
            break

    print(f"[OK] Hoan tat. Tong {total} diem da di tru sang '{args.target}'.")
    print("    Nho chay scripts/create_qdrant_indexes.py de tao payload index cho collection moi.")


if __name__ == "__main__":
    main()
