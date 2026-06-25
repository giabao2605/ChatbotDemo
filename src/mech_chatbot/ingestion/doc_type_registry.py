"""P2 - Chuan hoa NHAN LOAI TAI LIEU (document type) + da ngon ngu.

Van de truoc day: LoaiTaiLieu luu free-text tieng Viet KHONG dau tu LLM
("Ban ve gia cong", "So tay ISO"...) tron lan voi ma tieng Anh tu classifier
("technical_drawing", "invoice"...). Khong nhat quan -> kho loc/thong ke.

Giai phap: 1 bo MA CHUAN (canonical code) co nhan hien thi da ngon ngu (vi/en),
kem danh sach synonym (ke ca tieng Viet co/khong dau, tieng Anh) de chuan hoa
bat ky chuoi dau vao nao ve dung 1 ma.

Dung boi:
  - repository.save_page_metadata / update_document_full_metadata (chuan hoa khi luu)
  - ui/pages/documents.py, admin.py (hien thi nhat quan, ke ca du lieu cu)
"""
import re
import unicodedata

# code -> {"vi": <nhan tieng Viet co dau>, "en": <nhan tieng Anh>, "synonyms": [...]}
# synonyms nen viet thuong, khong dau (se duoc so khop sau khi bo dau).
DOC_TYPES = {
    "technical_drawing": {
        "vi": "Bản vẽ kỹ thuật", "en": "Technical drawing",
        "synonyms": ["technical drawing", "drawing", "ban ve", "ban ve ky thuat",
                     "ban ve gia cong", "ban ve co khi", "bản vẽ"],
    },
    "bom": {
        "vi": "Bảng kê vật tư (BOM)", "en": "Bill of materials",
        "synonyms": ["bom", "bill of materials", "bang ke", "bang ke vat tu",
                     "danh muc vat tu", "bảng kê vật tư"],
    },
    "process": {
        "vi": "Quy trình / Hướng dẫn", "en": "Process / Instruction",
        "synonyms": ["process", "procedure", "sop", "instruction", "quy trinh",
                     "huong dan", "so tay", "so tay iso", "work instruction"],
    },
    "catalog": {
        "vi": "Catalog / Tài liệu kỹ thuật", "en": "Catalog / Datasheet",
        "synonyms": ["catalog", "catalogue", "datasheet", "data sheet",
                     "tai lieu ky thuat", "thong so ky thuat"],
    },
    "invoice": {
        "vi": "Hóa đơn", "en": "Invoice",
        "synonyms": ["invoice", "hoa don", "hóa đơn"],
    },
    "contract": {
        "vi": "Hợp đồng", "en": "Contract",
        "synonyms": ["contract", "hop dong", "hợp đồng", "agreement"],
    },
    "payroll": {
        "vi": "Bảng lương", "en": "Payroll",
        "synonyms": ["payroll", "bang luong", "bảng lương", "luong", "salary"],
    },
    "decision": {
        "vi": "Quyết định", "en": "Decision",
        "synonyms": ["decision", "quyet dinh", "quyết định"],
    },
    "report": {
        "vi": "Báo cáo", "en": "Report",
        "synonyms": ["report", "bao cao", "báo cáo"],
    },
    "form": {
        "vi": "Biểu mẫu", "en": "Form",
        "synonyms": ["form", "bieu mau", "biểu mẫu", "mau don", "template"],
    },
    "generic": {
        "vi": "Tài liệu tổng hợp", "en": "General document",
        "synonyms": ["generic", "other", "khac", "tai lieu tong hop",
                     "tai lieu chung", "khong ro", "unknown"],
    },
}

DEFAULT_CODE = "generic"
SUPPORTED_LANGS = ("vi", "en")


def strip_accents(s):
    """Bo dau tieng Viet + ha thuong + gom khoang trang -> de so khop synonym."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


# Map synonym (da bo dau) -> code, build 1 lan.
_SYN_INDEX = None


def _syn_index():
    global _SYN_INDEX
    if _SYN_INDEX is None:
        idx = {}
        for code, meta in DOC_TYPES.items():
            idx[strip_accents(code)] = code
            idx[strip_accents(meta["vi"])] = code
            idx[strip_accents(meta["en"])] = code
            for syn in meta.get("synonyms", []):
                idx[strip_accents(syn)] = code
        _SYN_INDEX = idx
    return _SYN_INDEX


def normalize_doc_type(raw):
    """Tra ve canonical code, hoac None neu khong nhan dien duoc."""
    key = strip_accents(raw)
    if not key:
        return None
    idx = _syn_index()
    if key in idx:
        return idx[key]
    # So khop chua (substring) - uu tien synonym dai truoc
    for syn in sorted(idx.keys(), key=len, reverse=True):
        if syn and syn in key:
            return idx[syn]
    return None


def doc_type_label(code, lang="vi"):
    """Nhan hien thi cho 1 canonical code."""
    meta = DOC_TYPES.get(code)
    if not meta:
        return None
    return meta.get(lang) or meta.get("vi") or code


def canonical_label(raw, lang="vi"):
    """Chuan hoa 1 chuoi bat ky ve nhan hien thi chuan.
    Neu khong nhan dien -> giu nguyen raw (title-case nhe) de khong mat thong tin.
    """
    code = normalize_doc_type(raw)
    if code:
        return doc_type_label(code, lang)
    raw = (str(raw).strip() if raw else "")
    return raw or doc_type_label(DEFAULT_CODE, lang)


def list_doc_types(lang="vi"):
    """[{code, label}] cho UI (vd dropdown loc/sua)."""
    return [{"code": c, "label": doc_type_label(c, lang)} for c in DOC_TYPES]
