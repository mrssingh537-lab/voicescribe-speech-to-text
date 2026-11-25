import json
import logging
import requests
from typing import List, Tuple, Optional
from app.config import settings
from app.services.providers.base import TranscriptSegment

logger = logging.getLogger("voicescribe.translator")

# Mapping from language code / normalized code to canonical language name
LANGUAGE_NAME_MAP = {
    "en": "english",
    "hi": "hindi",
    "es": "spanish",
    "fr": "french",
    "de": "german",
    "ja": "japanese",
    "zh": "chinese simplified",
    "zh-cn": "chinese simplified",
    "zh-tw": "chinese traditional",
    "pt": "portuguese",
    "ar": "arabic",
    "ru": "russian",
    "it": "italian",
    "ko": "korean",
    "tr": "turkish",
    "nl": "dutch",
    "bn": "bengali",
    "ta": "tamil",
    "te": "telugu",
    "mr": "marathi",
    "ur": "urdu",
    "gu": "gujarati",
    "pa": "punjabi",
}

# Standard language code normalization for translation services
CODE_NORMALIZATION = {
    "zh": "zh-CN",
    "chinese": "zh-CN",
    "japanese": "ja",
    "hindi": "hi",
    "spanish": "es",
    "english": "en",
    "french": "fr",
    "german": "de",
    "arabic": "ar",
    "russian": "ru",
    "portuguese": "pt",
    "italian": "it",
    "korean": "ko",
    "turkish": "tr",
    "dutch": "nl",
    "bengali": "bn",
    "tamil": "ta",
    "telugu": "te",
    "marathi": "mr",
    "urdu": "ur",
    "gujarati": "gu",
    "punjabi": "pa",
}

# Shared HTTP session for connection pooling and fast keep-alive requests
_http_session: Optional[requests.Session] = None


def get_http_session() -> requests.Session:
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        _http_session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        })
    return _http_session


def normalize_code(code: Optional[str]) -> str:
    if not code:
        return "auto"
    cleaned = code.strip().lower()
    return CODE_NORMALIZATION.get(cleaned, cleaned)


def is_translation_needed(source_lang: Optional[str], target_lang: Optional[str]) -> bool:
    """
    Determines if translation is required between source_lang and target_lang.
    Preserves original transcript when target is 'auto' or matches source.
    """
    if not target_lang:
        return False
    tgt = normalize_code(target_lang)
    if tgt in ("auto", "none", "original", ""):
        return False

    src = normalize_code(source_lang)
    if src in ("auto", "unknown", ""):
        return True

    return src != tgt


def _translate_with_llm(texts: List[str], target_lang: str, source_lang: str = "auto") -> Optional[List[str]]:
    """
    Translates a list of strings in a single batch using the configured OpenAI / Groq API.
    Fast, highly cohesive, context-aware, and avoids third-party rate limits.
    """
    api_key = settings.effective_api_key
    if not api_key:
        return None

    tgt_norm = normalize_code(target_lang)
    tgt_name = LANGUAGE_NAME_MAP.get(tgt_norm, target_lang)

    api_url = getattr(settings, "TRANSCRIPTION_API_URL", "") or ""
    if "groq.com" in api_url:
        chat_url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.1-8b-instant"
    else:
        chat_url = "https://api.openai.com/v1/chat/completions"
        model = "gpt-4o-mini"

    system_prompt = (
        f"You are a professional subtitle translator. "
        f"Translate the provided JSON array of strings into {tgt_name}. "
        f"Preserve formatting, tone, and casing where appropriate. "
        f"Output strictly a JSON array of translated strings with the exact same number of items and order as input. "
        f"Do not include any explanation, notes, or markdown fences."
    )

    try:
        import httpx
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                chat_url,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(texts, ensure_ascii=False)}
                    ],
                    "temperature": 0.0
                }
            )
            if resp.status_code == 200:
                raw_content = resp.json()["choices"][0]["message"]["content"].strip()
                if raw_content.startswith("```"):
                    raw_content = raw_content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                translated_list = json.loads(raw_content)
                if isinstance(translated_list, list) and len(translated_list) == len(texts):
                    logger.info(f"[Translator] LLM translated {len(texts)} texts into '{tgt_name}' successfully.")
                    return [str(t) for t in translated_list]
    except Exception as e:
        logger.warning(f"[Translator] LLM translation failed: {e}. Falling back to web translators.")

    return None


def _translate_gtx(text: str, source_lang: str, target_lang: str) -> Optional[str]:
    """
    Fast Google GTX translation with connection pooling.
    Handles long text, punctuation, and all 100+ languages.
    """
    if not text or not text.strip():
        return text
    try:
        session = get_http_session()
        src = "auto" if not source_lang or source_lang in ("auto", "unknown") else normalize_code(source_lang)
        tgt = normalize_code(target_lang)

        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": src,
            "tl": tgt,
            "dt": "t",
            "q": text,
        }

        resp = session.get(url, params=params, timeout=7)
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                translated_parts = [part[0] for part in data[0] if part and part[0]]
                return "".join(translated_parts)
    except Exception as e:
        logger.debug(f"[Translator] Google GTX translation ({source_lang}->{target_lang}) failed: {e}")
    return None


def _translate_mymemory(text: str, source_lang: str, target_lang: str) -> Optional[str]:
    """
    Fallback translation using MyMemory via deep-translator or direct REST API.
    """
    if not text or not text.strip():
        return text

    src = normalize_code(source_lang)
    tgt = normalize_code(target_lang)

    # 1. Try deep-translator with mapped language names
    try:
        from deep_translator import MyMemoryTranslator
        src_name = "english" if src in ("auto", "unknown", "") else LANGUAGE_NAME_MAP.get(src, src)
        tgt_name = LANGUAGE_NAME_MAP.get(tgt, tgt)
        res = MyMemoryTranslator(source=src_name, target=tgt_name).translate(text)
        if res and res.strip() and not res.startswith("MYMEMORY WARNING:") and "INVALID SOURCE LANGUAGE" not in res:
            return res
    except Exception as e:
        logger.debug(f"[Translator] deep-translator MyMemory failed: {e}")

    # 2. Try direct MyMemory REST API with 2-letter codes
    try:
        session = get_http_session()
        src_code = "en" if src in ("auto", "unknown", "") else src
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": f"{src_code}|{tgt}"}
        resp = session.get(url, params=params, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            trans = data.get("responseData", {}).get("translatedText")
            if trans and trans.strip() and not trans.startswith("MYMEMORY WARNING:") and "INVALID" not in trans:
                return trans
    except Exception as e:
        logger.debug(f"[Translator] Direct MyMemory request failed: {e}")

    return None


def translate_text(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    """
    Translates text from source_lang to target_lang using a multi-layer strategy:
    1. LLM API (OpenAI/Groq if API key is configured)
    2. Google GTX API
    3. MyMemory (reliable backup)
    4. Graceful original text fallback if offline.
    """
    if not text or not text.strip():
        return text

    src = normalize_code(source_lang)
    tgt = normalize_code(target_lang)

    if src != "auto" and src == tgt:
        return text

    # Layer 1: LLM translation if API key is available
    if settings.effective_api_key:
        llm_res = _translate_with_llm([text], tgt, src)
        if llm_res and len(llm_res) == 1 and llm_res[0].strip():
            return llm_res[0]

    # Layer 2: Google GTX
    gtx_res = _translate_gtx(text, src, tgt)
    if gtx_res and gtx_res.strip():
        return gtx_res

    # Layer 3: MyMemory
    mymem_res = _translate_mymemory(text, src, tgt)
    if mymem_res and mymem_res.strip():
        return mymem_res

    # Layer 4: Graceful fallback
    logger.warning(f"[Translator] All translation backends failed for '{src}' -> '{tgt}'. Keeping original text.")
    return text


def translate_segments(
    segments: List[TranscriptSegment],
    source_lang: str,
    target_lang: str
) -> List[TranscriptSegment]:
    """
    Translates individual timestamped segments into the target language,
    preserving exact start/end timestamps, speaker labels, and word structures.
    Uses LLM batch translation if configured, or sequential translation with session reuse.
    """
    if not segments or not is_translation_needed(source_lang, target_lang):
        return segments

    src = normalize_code(source_lang)
    tgt = normalize_code(target_lang)

    logger.info(f"[Translator] Translating {len(segments)} segments from '{src}' to '{tgt}'...")

    # Layer 1: Batch LLM translation if API key is available (fastest, most accurate)
    if settings.effective_api_key:
        texts_to_translate = [seg.text for seg in segments]
        llm_results = _translate_with_llm(texts_to_translate, tgt, src)
        if llm_results and len(llm_results) == len(segments):
            return [
                TranscriptSegment(
                    start=seg.start,
                    end=seg.end,
                    text=trans_text,
                    speaker=seg.speaker,
                    words=seg.words
                )
                for seg, trans_text in zip(segments, llm_results)
            ]

    # Layer 2: Sequential translation with session pooling to prevent rate-limit 429 errors
    translated_segments = []
    for seg in segments:
        trans_text = translate_text(seg.text, source_lang=src, target_lang=tgt)
        translated_segments.append(
            TranscriptSegment(
                start=seg.start,
                end=seg.end,
                text=trans_text,
                speaker=seg.speaker,
                words=seg.words
            )
        )

    return translated_segments


def translate_transcript(
    segments: List[TranscriptSegment],
    full_text: str,
    source_lang: str,
    target_lang: str
) -> Tuple[List[TranscriptSegment], str]:
    """
    Translates both the timestamped segments and the overall transcript text.
    Ensures segment text and full_text remain cohesive and aligned in the target language.
    """
    if not is_translation_needed(source_lang, target_lang):
        return segments, full_text

    src = normalize_code(source_lang)
    tgt = normalize_code(target_lang)

    logger.info(f"[Translator] Translating transcript from '{src}' to '{tgt}'...")

    # 1. Translate segments
    translated_segments = translate_segments(segments, src, tgt)

    # 2. Build or translate cohesive full_text
    if translated_segments:
        translated_text = " ".join(seg.text.strip() for seg in translated_segments if seg.text.strip())
    else:
        translated_text = translate_text(full_text, source_lang=src, target_lang=tgt)

    logger.info(f"[Translator] Successfully translated transcript into '{tgt}'.")
    return translated_segments, translated_text
