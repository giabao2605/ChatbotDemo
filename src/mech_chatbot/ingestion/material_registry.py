"""P2 - Tu dien ma vat tu / dong nghia (DONG, quan tri qua UI).

Thay cho cac danh sach hardcode trc day:
  - mechanical_extractors.MATERIAL_PATTERNS  (regex trich xuat vat lieu)
  - repository.normalize_material_name        (chuan hoa ten vat lieu)
  - rag.service.KNOWN_MATERIALS               (guard chong bia vat lieu)

Doc tu bang dbo.MaterialDictionary + dbo.MaterialSynonym, co cache TTL ngan.
Neu DB rong / chua migrate / loi ket noi -> fallback ve gia tri mac dinh ben
duoi, dam bao KHONG BAO GIO lam gay luong ingest hoac RAG.
"""
import re
import time
import threading

from mech_chatbot.config.logging import logger

# Gia tri mac dinh (trung voi seed cua migration p2_material_dictionary.sql)
# (canonical_code, display_name, category, [synonyms])
_DEFAULTS = [
    ("SUS304", "SUS 304", "stainless steel", ["sus304", "ss304", "inox 304"]),
    ("SUS316", "SUS 316", "stainless steel", ["sus316", "ss316"]),
    ("SS400",  "SS400",   "carbon steel",    []),
    ("SPCC",   "SPCC",    "carbon steel",    []),
    ("AL6061", "AL 6061", "aluminum",        ["al6061", "a6061"]),
    ("A5052",  "A5052",   "aluminum",        ["al5052"]),
    ("S45C",   "S45C",    "carbon steel",    []),
    ("SKD11",  "SKD11",   "tool steel",      []),
    ("SKD61",  "SKD61",   "tool steel",      []),
]

# Tu dong nghia chung (text-level), giu tuong thich nguoc voi normalize cu
_GENERIC_SYNONYMS = {"inox": "stainless steel"}

_CACHE_TTL = 300  # giay
_lock = threading.Lock()
_cache = {"ts": 0.0, "materials": None}


def _load_from_db():
    """Tra ve list dict material tu DB, hoac None neu khong the doc/rong."""
    try:
        from sqlalchemy import text
        from mech_chatbot.db import repository as repo
        repo._ensure_engine()
        if repo.engine is None:
            return None
        materials = {}
        with repo.engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT MaterialID, CanonicalCode, DisplayName, Category "
                "FROM dbo.MaterialDictionary WHERE IsActive = 1"
            )).fetchall()
            for r in rows:
                materials[r[0]] = {
                    "code": r[1], "display": r[2],
                    "category": r[3], "synonyms": [],
                }
            if not materials:
                return None
            syn_rows = conn.execute(text(
                "SELECT MaterialID, Synonym FROM dbo.MaterialSynonym WHERE IsActive = 1"
            )).fetchall()
            for mid, syn in syn_rows:
                if mid in materials and syn:
                    materials[mid]["synonyms"].append(syn)
        return list(materials.values())
    except Exception as e:
        logger.warning(f"material_registry: khong doc duoc tu DB, dung mac dinh. ({e})")
        return None


def _defaults_as_list():
    return [
        {"code": c, "display": d, "category": cat, "synonyms": list(syn)}
        for (c, d, cat, syn) in _DEFAULTS
    ]


def _get_materials(force_refresh=False):
    now = time.time()
    if not force_refresh:
        with _lock:
            if (_cache["materials"] is not None
                    and (now - _cache["ts"]) < _CACHE_TTL):
                return _cache["materials"]
    data = _load_from_db()
    if not data:
        data = _defaults_as_list()
    with _lock:
        _cache["materials"] = data
        _cache["ts"] = now
    return data


def refresh_cache():
    """Goi sau khi admin sua tu dien de cap nhat ngay (xoa cache)."""
    _get_materials(force_refresh=True)


# ---------------------------------------------------------------------
# API dung boi cac module khac
# ---------------------------------------------------------------------
def get_known_materials():
    """List ma chuan (uppercase, khong space) - cho guard hallucination."""
    return [m["code"].upper().replace(" ", "") for m in _get_materials()]


def _token_to_regex(token):
    """SUS304 -> r'\\bSUS\\s*304\\b' ; cho phep khoang trang giua chu va so."""
    t = re.sub(r"\s+", "", str(token))
    parts = re.findall(r"[A-Za-z]+|\d+", t)
    if not parts:
        return None
    return r"\b" + r"\s*".join(re.escape(p) for p in parts) + r"\b"


def get_material_patterns():
    """List regex (string) de trich xuat vat lieu khoi text (thay MATERIAL_PATTERNS)."""
    patterns = []
    seen = set()
    for m in _get_materials():
        for tk in [m["code"]] + list(m.get("synonyms") or []):
            rx = _token_to_regex(tk)
            if rx and rx not in seen:
                seen.add(rx)
                patterns.append(rx)
    return patterns


def _synonym_map():
    """{synonym_lower: display_lower} + generic synonyms."""
    mp = {}
    for m in _get_materials():
        disp = (m["display"] or m["code"]).strip().lower()
        mp[m["code"].strip().lower()] = disp
        for syn in (m.get("synonyms") or []):
            mp[str(syn).strip().lower()] = disp
    for k, v in _GENERIC_SYNONYMS.items():
        mp.setdefault(k, v)
    return mp


def normalize_material(raw):
    """Chuan hoa ten vat lieu ve dang canonical (display). Thay normalize_material_name."""
    if not raw:
        return None
    s = str(raw).strip().lower()
    s = re.sub(r"\s+", " ", s)
    mp = _synonym_map()
    if s in mp:
        return mp[s]
    # Thay the synonym (uu tien synonym dai truoc de tranh thay nham)
    for syn in sorted(mp.keys(), key=len, reverse=True):
        if syn and syn in s:
            s = s.replace(syn, mp[syn])
    return re.sub(r"\s+", " ", s).strip()
