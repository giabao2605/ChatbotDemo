import os
import threading
import time
from google import genai
from google.genai import errors as genai_errors
from tenacity import RetryError

DEFAULT_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")
_PLACEHOLDER_KEY = "DIEN_KEY_CUA_BAN_VAO_DAY"
_GEMINI_CALL_LOCK = threading.Lock()
_LAST_GEMINI_CALL_AT = 0.0

def is_retryable_error(exc) -> bool:
    """Retry khi bi rate-limit (429) hoac loi server (5xx) cua Gemini (google-genai)."""
    if isinstance(exc, genai_errors.APIError):
        code = getattr(exc, "code", None)
        return code == 429 or (isinstance(code, int) and code >= 500)
    return False

def _unwrap_retry_error(exc):
    if isinstance(exc, RetryError):
        try:
            return exc.last_attempt.exception()
        except Exception:
            return exc
    return exc

def describe_gemini_error(exc) -> str:
    """Mo ta loi goc cua Gemini thay vi chi hien RetryError chung chung."""
    root = _unwrap_retry_error(exc)
    code = getattr(root, "code", None) or getattr(root, "status_code", None)
    status = getattr(root, "status", None)
    message = getattr(root, "message", None) or str(root)
    parts = [type(root).__name__]
    if code is not None:
        parts.append(f"code={code}")
    if status:
        parts.append(f"status={status}")
    if message:
        parts.append(f"message={message}")
    if root is not exc:
        return f"{type(exc).__name__} -> " + ", ".join(parts)
    return ", ".join(parts)

def _throttle_gemini_call():
    """Giam nguy co 429 khi re-ingest nhieu ban ve lien tiep."""
    try:
        min_interval = float(os.getenv("GEMINI_MIN_INTERVAL_SECONDS", "6"))
    except ValueError:
        min_interval = 6.0
    if min_interval <= 0:
        return

    global _LAST_GEMINI_CALL_AT
    with _GEMINI_CALL_LOCK:
        now = time.monotonic()
        wait_for = min_interval - (now - _LAST_GEMINI_CALL_AT)
        if wait_for > 0:
            time.sleep(wait_for)
        _LAST_GEMINI_CALL_AT = time.monotonic()

class GeminiVisionModel:
    """
    Wrapper giu NGUYEN interface cu `.generate_content(...)` de cac call-site
    (rag_logic / pdf_processor) khong phai doi logic khi migrate sang google-genai.
    """

    def __init__(self, api_key: str, model_name: str = DEFAULT_VISION_MODEL):
        self._client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate_content(self, contents):
        # contents co the la str (chi prompt) hoac list [prompt, PIL.Image]
        _throttle_gemini_call()
        parts = list(contents) if isinstance(contents, (list, tuple)) else [contents]
        return self._client.models.generate_content(
            model=self.model_name,
            contents=parts,
        )

def build_vision_model(model_name: str = DEFAULT_VISION_MODEL):
    """Tra ve GeminiVisionModel neu co API key hop le, nguoc lai None."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key and api_key != _PLACEHOLDER_KEY:
        return GeminiVisionModel(api_key, model_name)
    return None
