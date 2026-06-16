import sys
import io
import os
import base64
import re
import warnings
import time
import uuid
 
# Tat toan bo canh bao rac
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", category=FutureWarning)
 
from dotenv import load_dotenv
load_dotenv()
 
from logger_config import logger
from PIL import Image
import underthesea
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse, RetrievalMode
from tenacity import retry, retry_if_exception_type, retry_if_exception, wait_exponential, stop_after_attempt
from langchain_cohere import ChatCohere, CohereRerank
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
import json
 
logger.info("Dang khoi dong he thong RAG AI...")
 
# ==========================================
# 1. KET NOI DB VA MODELS (Cohere + Local Embedding)
# ==========================================
import threading
import atexit
from functools import lru_cache
from gemini_client import build_vision_model, is_retryable_error
 
_VISION_MODEL = build_vision_model()
 
RERANK_PER_PART = int(os.getenv("RERANK_PER_PART", "10"))
RERANK_TOP_N_CAP = int(os.getenv("RERANK_TOP_N_CAP", "40"))
 
@lru_cache(maxsize=4)
def get_reranker(top_n):
    return CohereRerank(
        cohere_api_key=os.getenv("COHERE_API_KEY"),
        model="rerank-multilingual-v3.0",
        top_n=top_n
    )
 
class RAGSystem:
    _instance = None
    _lock = threading.Lock()
 
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls._init_components()
        return cls._instance
 
    @staticmethod
    def _init_components():
        # Uu tien QDRANT_URL (Qdrant Server mode), fallback ve local path neu khong co
        qdrant_url = os.getenv("QDRANT_URL", "")
        qdrant_path = os.getenv("QDRANT_PATH", "./Mechanical_Qdrant_DB")
        if qdrant_url:
            logger.info(f"   -> Ket noi Qdrant Server tai: {qdrant_url}")
            client = QdrantClient(url=qdrant_url)
        else:
            logger.info(f"   -> Dung Qdrant Local tai: {qdrant_path}")
            client = QdrantClient(path=qdrant_path)
 
        logger.info("   -> Dang tai model Embedding chuyen Tieng Viet (keepitreal/vietnamese-sbert)...")
        embed_model = os.getenv("EMBEDDING_MODEL", "keepitreal/vietnamese-sbert")
        embeddings = HuggingFaceEmbeddings(model_name=embed_model)
 
        logger.info("   -> Dang khoi tao mo hinh BM25 (Qdrant/bm25)...")
        sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
 
        if not client.collection_exists("TaiLieuKyThuat_v2"):
            logger.info("   -> Collection 'TaiLieuKyThuat_v2' khong ton tai. Dang tao moi...")
            client.create_collection(
                collection_name="TaiLieuKyThuat_v2",
                vectors_config=models.VectorParams(
                    size=768,
                    distance=models.Distance.COSINE
                ),
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=False,
                        )
                    )
                }
            )
 
        vectorstore = QdrantVectorStore(
            client=client,
            collection_name="TaiLieuKyThuat_v2",
            embedding=embeddings,
            sparse_embedding=sparse_embeddings,
            sparse_vector_name="sparse",
            retrieval_mode=RetrievalMode.HYBRID
        )
 
        logger.info("   -> Dang ket noi Cohere Command R...")
        llm_model = os.getenv("COHERE_MODEL_NAME", "command-r-08-2024")
        llm = ChatCohere(
            model=llm_model,
            temperature=0,
            max_tokens=4000,
            cohere_api_key=os.getenv("COHERE_API_KEY")
        )
 
        return client, vectorstore, llm
 
client, vectorstore, llm = RAGSystem.get_instance()
 
# FIX H6: Nguong score cutoff cho rerank dua ra config (env) thay vi hardcode 0.3
RERANK_SCORE_CUTOFF = float(os.getenv("RERANK_SCORE_CUTOFF", "0.3"))
 
# FIX H5: Cache ket qua word_tokenize (underthesea rat cham 50-200ms/call).
# Cau hoi / chunk lap lai se khong phai tokenize lai.
@lru_cache(maxsize=4096)
def tokenize_cached(text):
    return underthesea.word_tokenize(text, format="text")
 
# FIX H7: Cohere Free Tier de bi 429 Too Many Requests.
# Bo sung retry + backoff cho call Cohere (HyDE, rerank). Truoc day chi Gemini co retry.
def _is_cohere_rate_limit(exc):
    msg = str(exc).lower()
    return "429" in msg or "too many requests" in msg or "rate limit" in msg
 
@retry(
    retry=retry_if_exception(_is_cohere_rate_limit),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    stop=stop_after_attempt(4),
)
def cohere_invoke(messages):
    return llm.invoke(messages)
 
@retry(
    retry=retry_if_exception(_is_cohere_rate_limit),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    stop=stop_after_attempt(4),
)
def cohere_rerank(compressor, documents, query):
    return compressor.compress_documents(documents=documents, query=query)
 
# =========================================
# 2. PROMPT CUC KY NGHIEM NGAT - CHI TRA LOI TU DU LIEU NAP SAN
# ==========================================
system_prompt = (
    "Ban la Ky Su Truong Thiet Ke Co Khi. Nhiem vu cua ban la ho tro giai dap ky thuat chuyen sau dua TREN TAI LIEU CO SAN.\n\n"
    "=== DU LIEU BAN VE / TAI LIEU (TU QDRANT) ===\n"
    "{context}\n\n"
    "=== LICH SU TRO CHUYEN GAN DAY ===\n"
    "{chat_history_str}\n\n"
    "=== QUY TAC PHAN HOI (TUAN THU TUYET DOI) ===\n"
    "1. NOI CO SACH, MACH CO CHUNG: Moi thong so (kich thuoc, dung sai, vat lieu) phai trich xuat chinh xac tu phan 'DU LIEU BAN VE'. Tuyet doi khong tu bia thong so.\n"
    "2. CACH TU CHOI THONG MINH: Neu 'DU LIEU BAN VE' rong (khong co) hoac khong nhac den thong tin nguoi dung hoi, BẮT BUỘC PHẢI TRẢ LỜI: 'Bản vẽ/Tài liệu hiện tại không ghi chú thông tin về...'. TUYET DOI KHONG SU DUNG KIEN THUC BEN NGOAI DE BIA RA CAU TRA LOI!\n"
    "3. XU LY TU KHOA NGAN: Neu nguoi dung chi go vai tu khoa (vd: 'inox 304', 'dung sai'), hay tu dong tong hop tat ca chi tiet lien quan den tu khoa do trong tai lieu thanh mot bao cao ngan gon.\n"
    "4. PHAN BIET VAT LIEU CHINH & PHU: Luon tach bach ro rang giua 'Vat lieu chinh cua cum/thanh pham' va 'Vat lieu cua linh kien phu/bulong/oc vit'. Khong duoc lay vat lieu linh kien nho gan cho toan bo san pham.\n"
    "5. UU TIEN KE BANG: Luon su dung Bang (Markdown Table) khi liet ke cac linh kien trong Bang ke vat tu, hoac khi duoc yeu cau SO SANH nhieu ma ban ve voi nhau.\n"
    "6. DI THANG VAO VAN DE: Luoc bo cac cau rao truoc don sau (vd: 'Theo tai lieu cung cap...'). Tra loi nhu mot ky su chuyen nghiep: Suc tich, Ro rang, Diem nhan vao cac thong so.\n"
)
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{question}"),
])
 
def format_docs(docs):
    """Format documents kem thong tin nguon ro rang de LLM co the trich dan va so sanh."""
    formatted_texts = []
    for doc in docs:
        source_file = doc.metadata.get('file_goc', 'Khong ro nguon')
        trang = doc.metadata.get('trang_so', '?')
        cong_doan = doc.metadata.get('cong_doan', '')
        loai = doc.metadata.get('loai_du_lieu', '')
 
        # FIX: metadata thuc te luu ma o 'ma_doi_tuong' (list), khong phai ma_thanh_pham/ma_ban_thanh_pham
        # -> truoc day header luon ra 'CHUNG'. Gio doc dung key.
        ma_doi_tuong = doc.metadata.get('ma_doi_tuong', [])
        if isinstance(ma_doi_tuong, (list, tuple)):
            ma_str = ", ".join(str(m) for m in ma_doi_tuong if m and str(m) != "Khong ro")
        else:
            ma_str = str(ma_doi_tuong) if ma_doi_tuong and str(ma_doi_tuong) != "Khong ro" else ""
 
        # DAT MA LEN DAU DE LLM DE PHAN BIET KHI SO SANH CHEO
        header = "[TAI LIEU "
        if ma_str:
            header += f"MA {ma_str}"
        else:
            header += "CHUNG"
        header += "]\n"
 
        header += f"- Nguon: {source_file} (Trang {trang}) | Cong doan: {cong_doan} | Phan loai: {loai}"
 
        # FIX #3: uu tien noi dung goc (chua tokenize BM25) cho LLM, fallback ve page_content
        noi_dung = doc.metadata.get("noi_dung_goc", doc.page_content)
        formatted_texts.append(f"{header}\n- Noi dung: {noi_dung}")
    return "\n\n---\n\n".join(formatted_texts)
 
# ==========================================
# 3. HAM HO TRO: PHAN TICH CAU HOI DE LAY INTENT (MA DOI TUONG)
# ==========================================
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
 
_INTENT_MAX_WORKERS = int(os.getenv("INTENT_MAX_WORKERS", "8"))
_INTENT_TIMEOUT = float(os.getenv("INTENT_TIMEOUT", "6.0"))
 
# FIX: Executor dung chung o cap module.
# Truoc day dung 'with ThreadPoolExecutor() as executor' ben trong ham: khi future.result(timeout)
# bi timeout, __exit__ cua 'with' goi shutdown(wait=True) va BLOCK toi khi call_llm xong
# -> timeout gan nhu vo tac dung. Dung executor module-level, khong boc 'with'.
_INTENT_EXECUTOR = ThreadPoolExecutor(max_workers=_INTENT_MAX_WORKERS)
atexit.register(_INTENT_EXECUTOR.shutdown, wait=False)
 
def extract_search_intent(question, current_part_ids=None):
    """Phan tich cau hoi de lay danh sach ma doi tuong bang LLM (co timeout)."""
    if current_part_ids is None:
        current_part_ids = []
 
    extracted_codes = []
 
    prompt_intent = f"""
    Trich xuat tat ca cac ma so ban ve/linh kien/tieu chuan ma nguoi dung dang nhac toi trong cau hoi: '{question}'.
    Tra ve MOT MANG JSON CAC CHUOI theo dung quy tac sau:
    1. Neu cau hoi co nhac ma so (vd 9.3.03844, 8.3.xxx), tra ve mang cac ma: ["9.3.03844"]
    2. Neu cau hoi la xa giao (chao, cam on, hoi ten, thoi tiet, cac chu de khong lien quan ky thuat), tra ve: ["CHITCHAT"]
    3. Neu cau hoi co lien quan ky thuat nhung khong chi dinh ma cu the, tra ve: []
 
    Luu y: Chi tra ve JSON, khong giai thich gi them.
    """
 
    # FIX H4: Regex-first. Neu cau hoi da chua ma ban ve (vd 9.3.03844, 8.3.xxxxx.xxx)
    # thi trich bang regex va BO QUA hoan toan LLM intent -> tiet kiem 1 API call moi cau.
    regex_codes = re.findall(r'\b\d{1,2}\.\d{1,2}\.\d{3,}(?:\.\d+)?\b', question)
    if regex_codes:
        seen_rc = set()
        extracted_codes = []
        for c in regex_codes:
            if c not in seen_rc:
                seen_rc.add(c)
                extracted_codes.append(c)
        logger.info(f"H4: Trich ma bang regex (bo qua LLM intent): {extracted_codes}")
    else:
        # Khong co ma -> fallback goi LLM nhu cu (van detect CHITCHAT, co timeout)
        # HumanMessage da duoc import o dau file
        def call_llm():
            response = llm.invoke([HumanMessage(content=prompt_intent)])
            return response.content
 
        try:
            future = _INTENT_EXECUTOR.submit(call_llm)
            # Timeout de tranh lam treo ung dung nhung van du thoi gian cho API
            raw_response = future.result(timeout=_INTENT_TIMEOUT)
 
            # json da duoc import o dau file
            clean_json = raw_response.replace('```json', '').replace('```', '').strip()
            parsed_codes = json.loads(clean_json)
            if isinstance(parsed_codes, list):
                extracted_codes = [str(c) for c in parsed_codes if c]
        except concurrent.futures.TimeoutError:
            logger.warning(f"LLM Intent Extraction bi timeout (qua {_INTENT_TIMEOUT}s). Roi vao Hybrid Search mac dinh.")
        except Exception as e:
            logger.warning(f"Loi LLM Intent Extraction: {e}. Roi vao Hybrid Search mac dinh.")
 
    # Co che cap nhat State (co tracking "inherited" de xu ly hoi thoai dai)
    if extracted_codes:
        new_part_ids = extracted_codes  # Co ma moi -> ghi de state
        is_inherited = False
    else:
        new_part_ids = current_part_ids  # Khong co ma moi -> Dung state cu
        is_inherited = True
 
    if not new_part_ids:
        return None, [], True
 
    # Dung MatchAny cho truong array metadata.ma_doi_tuong
    qdrant_filter = models.Filter(
        should=[
            models.FieldCondition(
                key="metadata.ma_doi_tuong",
                match=models.MatchAny(any=new_part_ids)
            )
        ]
    )
    return qdrant_filter, new_part_ids, is_inherited
 
def rerank_docs(docs):
    priority = {
        "title_block": 0,
        "bang_ke_vat_tu": 1,
        "yckt": 2,
        "hdcv": 3,
        "text": 4,
        "image_summary": 5,
    }
    return sorted(docs, key=lambda d: priority.get(d.metadata.get("loai_du_lieu", "text"), 4))
 
def long_context_reorder(docs):
    """
    Sap xep lai tai lieu de chong 'Lost in the Middle' cua LLaMA.
    Gia dinh docs da duoc sort theo do uu tien (tu cao xuong thap).
    Mang reorder se xen ke: Rank 1 o dau, Rank 2 o cuoi, Rank 3 o sat dau, Rank 4 o sat cuoi...
    """
    if len(docs) <= 2:
        return docs
 
    reordered = [None] * len(docs)
    left = 0
    right = len(docs) - 1
    for i, doc in enumerate(docs):
        if i % 2 == 0:
            reordered[left] = doc
            left += 1
        else:
            reordered[right] = doc
            right -= 1
    return reordered
 
# ==========================================
# 4. HAM XU LY LOI (TRAI TIM CUA CHATBOT)
# ==========================================
def chat_with_rag(user_question, image_path=None, chat_history=None, current_part_ids=None):
    if chat_history is None:
        chat_history = []
 
    # Tao chuoi lich su (Token-Budgeted Windowing) de nap vao prompt cho mach lac hoi thoai
    # FIX HOI THOAI DAI: Thay vi co dinh 4 message (bot response dai chiem hang ngan token,
    # lan at context tai lieu khien LLM tra loi kem), dung budget ky tu co dinh.
    chat_history_str = ""
    HISTORY_BUDGET = 1500  # ~375 tokens - du giu mach hoi thoai, khong lan at context
    recent_history = chat_history[-6:]  # Xet nhieu message hon nhung cat theo budget
 
    built_parts = []
    budget_used = 0
    for msg in reversed(recent_history):  # Uu tien tin nhan moi nhat
        role = "Khach" if msg["role"] == "user" else "Bot"
        content = msg['content']
        # Bot response thuong rat dai (bang, trich dan) -> cat manh tay
        if role == "Bot" and len(content) > 400:
            cut_pos = content[:400].rfind('.')
            content = (content[:cut_pos + 1] if cut_pos > 50 else content[:400]) + " [...]"
        elif role == "Khach" and len(content) > 200:
            content = content[:200] + " [...]"
        line = f"{role}: {content}\n"
        if budget_used + len(line) > HISTORY_BUDGET:
            break
        built_parts.append(line)
        budget_used += len(line)
    chat_history_str = "".join(reversed(built_parts))
 
    # BUOC A: XU LY ANH BANG GEMINI
    image_analysis = ""
    if image_path:
        logger.info("Dang dung Gemini de phan tich anh tai len...")
        if _VISION_MODEL:
            try:
                img_to_analyze = Image.open(image_path)
                prompt = f"Nguoi dung tai len mot hinh anh va hoi: '{user_question}'. Hay mo ta chinh xac va chi tiet nhung gi ban thay trong anh nay de lam ngu canh tra loi. Neu do la ma code hay giao dien phan mem, hay noi ro. Tra loi bang tieng Viet."
 
                @retry(
                    retry=retry_if_exception(is_retryable_error),
                    wait=wait_exponential(multiplier=2, min=2, max=30),
                    stop=stop_after_attempt(5)
                )
                def call_gemini():
                    return _VISION_MODEL.generate_content([prompt, img_to_analyze])
 
                response = call_gemini()
                image_analysis = response.text
                logger.info("Phan tich anh bang Gemini thanh cong.")
            except Exception as e:
                logger.error(f"Loi khi doc anh bang Gemini: {e}", exc_info=True)
        else:
            logger.warning("Chua co API Key Gemini hop le, bo qua phan tich anh.")
 
    # BUOC B: TIM KIEM THONG MINH KET HOP STATE MEMORY
    from pdf_processor import remove_accents
    text_clean_check = re.sub(r'[^\w\s]', '', remove_accents(user_question.lower())).strip()
    chitchat_words_check = {"xin chao", "chao", "hi", "hello", "cam on", "thank", "thanks", "ok", "da", "vang", "tam biet", "bye", "alo", "chao ban"}
    is_chitchat = text_clean_check in chitchat_words_check
 
    retrieved_docs = []
    skip_retrieval = False
    query_to_search = user_question  # Mac dinh, cac nhanh ben duoi se override neu can
 
    if is_chitchat:
        logger.info("Cau hoi la giao tiep co ban, bo qua truy xuat DB.")
        new_part_ids = current_part_ids
        skip_retrieval = True
    else:
        logger.info("Dang phan tich intent de tim kiem du lieu...")
        qdrant_filter, new_part_ids, is_inherited = extract_search_intent(user_question, current_part_ids)
 
        if new_part_ids == ["CHITCHAT"]:
            logger.info("LLM xac nhan la cau hoi ngoai le/xa giao. Bo qua toan bo Retrieval va HyDE.")
            new_part_ids = current_part_ids  # Giu nguyen state cu
            qdrant_filter = None
            skip_retrieval = True
        else:
            # Tien xu ly cau hoi bang underthesea de match voi du lieu BM25
            tokenized_question = tokenize_cached(user_question)
            query_to_search = tokenized_question
 
            # HyDE (Hypothetical Document Embeddings) Trigger
            # TOI UU SIEU TOC: Chi bat HyDE neu KHONG CO ma ban ve cu the. Neu da co ma, BM25 du suc tim ra.
            # Nang nguong tu 15 len 25 tu de phu hop hon voi tieng Viet (Fix Bug #11)
            if len(tokenized_question.split()) < 25 and not new_part_ids:
                logger.info("Cau hoi ngan VA khong co ma ban ve, kich hoat HyDE de mo rong ngu canh...")
                try:
                    # HumanMessage da duoc import o dau file
                    hyde_prompt = f"Viet mot doan van ban ky thuat ngan gon (1-2 cau) tra loi cho cau hoi sau trong linh vuc gia cong co khi: '{user_question}'"
                    hyde_response = cohere_invoke([HumanMessage(content=hyde_prompt)]).content
                    query_to_search = tokenize_cached(hyde_response)
                except Exception as e:
                    logger.warning(f"Loi HyDE: {e}")
 
            if new_part_ids and qdrant_filter:
                if is_inherited:
                    # FIX HOI THOAI DAI: State ke thua tu luot truoc - user co the da doi chu de.
                    # Tim SONG SONG: theo filter cu + toan DB, gop ket qua de Rerank quyet dinh.
                    logger.info(f"State ke thua ({new_part_ids}). Dual search: filtered + unfiltered...")
                    try:
                        ret_filtered = vectorstore.as_retriever(
                            search_type="similarity",
                            search_kwargs={"k": 8, "filter": qdrant_filter}
                        )
                        ret_unfiltered = vectorstore.as_retriever(
                            search_type="similarity",
                            search_kwargs={"k": 8}
                        )
                        docs_f = ret_filtered.invoke(query_to_search)
                        docs_u = ret_unfiltered.invoke(query_to_search)
                        # Merge + deduplicate (uu tien filtered truoc)
                        seen = set()
                        for doc in docs_f + docs_u:
                            key = doc.page_content[:200]
                            if key not in seen:
                                seen.add(key)
                                retrieved_docs.append(doc)
                    except Exception as e:
                        logger.warning(f"Dual retrieval that bai: {e}")
                else:
                    # MA MOI DUOC TRICH XUAT: Tim chinh xac theo filter
                    base_k = 15 * len(new_part_ids)
                    logger.info(f"Dang truy xuat cho cac ma: {new_part_ids} (k={base_k})...")
                    try:
                        retriever = vectorstore.as_retriever(
                            search_type="similarity",
                            search_kwargs={"k": base_k, "filter": qdrant_filter}
                        )
                        retrieved_docs = retriever.invoke(query_to_search)
                    except Exception as e:
                        logger.warning(f"Retrieval that bai cho cac ma {new_part_ids}: {e}")
            else:
                # Tim kiem chung neu khong co ma
                base_k = 30
                logger.info(f"Khong co ma cu the, dang tim kiem tren toan bo Database (Pure Hybrid Search) k={base_k}...")
                retriever = vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": base_k}
                )
                retrieved_docs = retriever.invoke(query_to_search)
 
    # Fallback (Thoat trang thai neu tim theo State khong ra ket qua)
    if not skip_retrieval and not retrieved_docs and new_part_ids:
        logger.info("Cac filter khong tim thay tai lieu nao, thu tim toan bo DB (Fallback)...")
        base_k = 30
        retriever_no_filter = vectorstore.as_retriever(
            search_type="similarity",  # Hybrid mode dung similarity (Fix Bug #5)
            search_kwargs={"k": base_k}
        )
        retrieved_docs = retriever_no_filter.invoke(query_to_search)
 
    if image_analysis:
        fake_doc = Document(
            page_content=f"Phan tich noi dung anh nguoi dung tai len: {image_analysis}",
            metadata={
                "file_goc": "Anh dinh kem tu nguoi dung",
                "loai_du_lieu": "image_summary",
                "trang_so": "1",
                "cong_doan": "Anh truc tiep"
            }
        )
        retrieved_docs.insert(0, fake_doc)
 
    if not retrieved_docs and not is_chitchat and not skip_retrieval:
        logger.info("Canh bao: Khong tim thay tai lieu Qdrant nao. Chuyen cho LLM tu xu ly tu choi thong minh.")
 
    # BUOC B2: CROSS-ENCODER RE-RANK & REORDER (CHONG LOST IN THE MIDDLE)
    if retrieved_docs:
        # Tach fake_doc (anh nguoi dung upload) ra khoi qua trinh rerank
        fake_docs = [d for d in retrieved_docs if d.metadata.get("loai_du_lieu") == "image_summary" and d.metadata.get("file_goc") == "Anh dinh kem tu nguoi dung"]
        real_docs = [d for d in retrieved_docs if d not in fake_docs]
 
        if real_docs and os.getenv("COHERE_API_KEY"):
            try:
                target_top_n = RERANK_PER_PART * max(1, len(new_part_ids) if new_part_ids else 1)
                
                # MUC A: Nhan dien tu khoa liet ke de mo rong top_n, tranh bi cat cong doan
                from pdf_processor import remove_accents
                q_norm = remove_accents(user_question.lower())
                list_keywords = ["toan bo", "tat ca", "quy trinh", "liet ke"]
                if any(kw in q_norm for kw in list_keywords):
                    target_top_n = max(target_top_n, 25)
                    logger.info(f"Phat hien tu khoa liet ke, mo rong target_top_n len {target_top_n}")

                top_n = min(RERANK_TOP_N_CAP, target_top_n)
                compressor = get_reranker(top_n)
 
                logger.info(f"Dang su dung Cohere Rerank de filter {len(real_docs)} tai lieu (top_n={top_n})...")
                compressed_docs = cohere_rerank(compressor, real_docs, user_question)
                
                # LOP PHONG THU 1: Score Cutoff
                # Chi lay cac tai lieu co relevance_score >= 0.3 (da duoc calibrated boi Cohere)
                real_docs = [doc for doc in compressed_docs if doc.metadata.get("relevance_score", 1.0) >= RERANK_SCORE_CUTOFF]
                
                if not real_docs:
                    logger.info("Tat ca tai lieu deu duoi nguong relevance_score. Xoa context de chong hallucination.")
            except Exception as e:
                logger.error(f"Loi khi su dung Cohere Rerank: {e}. Fallback to manual rerank.")
                real_docs = rerank_docs(real_docs)
        else:
            real_docs = rerank_docs(real_docs)

        # LOP PHONG THU 1 (CODE): Chan hoan toan LLM neu khong co tai lieu that (va khong phai chitchat/co anh)
        if not real_docs and not fake_docs:
            logger.warning("BLOCKER: Context rong, chan goi LLM de tranh Hallucination.")
            empty_msg = "Tài liệu hiện tại không ghi chú thông tin về câu hỏi của bạn. Vui lòng kiểm tra lại hoặc cung cấp thêm bản vẽ."
            def mock_stream():
                yield empty_msg
            return mock_stream(), "", [], new_part_ids

        retrieved_docs = fake_docs + real_docs

        retrieved_docs = long_context_reorder(retrieved_docs)

    # BUOC C: SINH CAU TRA LOI (STREAMING)
    context_text = format_docs(retrieved_docs)
    logger.info(f"Da tim thay {len(retrieved_docs)} tai lieu lien quan. Dang phan tich...")

    chain = prompt_template | llm | StrOutputParser()

    stream = chain.stream({
        "context": context_text,
        "question": user_question,
        "chat_history_str": chat_history_str
    })
 
    # BUOC D: TU DONG TAO TRICH DAN NGUON VA HINH ANH (Tra ve cung stream)
    ref_text, ref_images = build_source_citations(retrieved_docs)
 
    return stream, ref_text, ref_images, new_part_ids
 
def build_source_citations(docs):
    references = []
    ref_images = []
    for doc in docs:
        source = doc.metadata.get('file_goc', 'Khong ro')
        page = doc.metadata.get('trang_so', '?')
        cong_doan = doc.metadata.get('cong_doan', 'Khong ro')
        loai = doc.metadata.get('loai_du_lieu', '')
        # Lay thu_muc de reconstruct ten file anh dung format (Fix Bug #7)
        thu_muc = doc.metadata.get('phong_ban_quyen', '')
 
        cite = f"**{source}** (Trang {page}) - {cong_doan}"
        if loai == 'image_summary':
            cite += " *(phan tich hinh anh)*"
        if cite not in references:
            references.append(cite)
 
        # Trich xuat duong dan anh tham chieu
        # Format luu: {safe_thu_muc}_{ten_file_ko_ext}_page{N}.png
        if source != 'Anh dinh kem tu nguoi dung':
            safe_thu_muc = re.sub(r'[\\/*?:"<>|]', "", thu_muc) if thu_muc else ""
            base_name = os.path.splitext(str(source))[0]
            if safe_thu_muc:
                img_name = f"{safe_thu_muc}_{base_name}_page{page}.png"
            else:
                img_name = f"{base_name}_page{page}.png"
 
            img_path = os.path.join("Data_Anh_Da_Tach", img_name)
            if img_path not in ref_images and os.path.exists(img_path):
                ref_images.append(img_path)
 
    if not references:
        return "", []
 
    ref_text = "\n\n---\n**Nguon tham chieu:**\n" + "\n".join([f"- {r}" for r in references])
    return ref_text, ref_images
 
# ==========================================
# 5. KHU VUC TEST THU CHUC NANG
# ==========================================
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("HE THONG RAG DEMO DA SAN SANG (Cohere + Local Embedding)")
    print("=" * 50)
 
    print("\n--- TEST: HOI VE DUNG SAI VAT LIEU ---")
    stream, ref_text, ref_images, parts = chat_with_rag("Dung sai do day vat lieu la bao nhieu?")
    print("\nBot tra loi: ", end="")
    for chunk in stream:
        print(chunk, end="")
    print("\n" + ref_text)
