import os
import re
from typing import Optional
import requests

LANGUAGE_LOCALE_MAP = {
    "hi": "hi",
    "mr": "mr",
    "bn": "bn",
    "en": "en",
    "te": "te",
    "ta": "ta",
    "gu": "gu"
}

def split_text_into_chunks(text: str, max_chars: int = 140) -> list:
    """Splits text into naturally paced sentence chunks under max_chars for TTS."""
    clean_text = re.sub(r'\s+', ' ', text).strip()
    if not clean_text:
        return []
    
    # Split on sentence boundaries (., !, ?, |, ।, newline)
    sentences = re.split(r'([.!?।|\n]+)', clean_text)
    chunks = []
    current = ""
    
    for s in sentences:
        if not s:
            continue
        if len(current) + len(s) < max_chars:
            current += s
        else:
            if current.strip():
                chunks.append(current.strip())
            current = s
            
    if current.strip():
        chunks.append(current.strip())
        
    # If any single chunk exceeds max_chars, split on spaces
    final_chunks = []
    for c in chunks:
        if len(c) <= max_chars:
            final_chunks.append(c)
        else:
            words = c.split(' ')
            sub = ""
            for w in words:
                if len(sub) + len(w) + 1 <= max_chars:
                    sub += (" " if sub else "") + w
                else:
                    if sub:
                        final_chunks.append(sub)
                    sub = w
            if sub:
                final_chunks.append(sub)
                
    return final_chunks

def synthesize_speech_audio(text: str, language: str = "hi") -> bytes:
    """
    Synthesizes authentic spoken audio bytes for the given text.
    Supports Hindi (hi), Marathi (mr), Bengali (bn), English (en), and other Indic languages.
    Uses OpenAI TTS if OPENAI_API_KEY is configured in environment,
    or falls back to high-resilience Google TTS audio synthesis.
    Returns bytes of MP3 audio.
    """
    if not text or not text.strip():
        return b""

    lang = LANGUAGE_LOCALE_MAP.get(language.lower(), "hi")
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()

    # 1. Cloud OpenAI TTS (if API key present)
    if openai_key and len(text) < 4000:
        try:
            resp = requests.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "tts-1",
                    "input": text.strip()[:4000],
                    "voice": "alloy"
                },
                timeout=12
            )
            if resp.status_code == 200 and resp.content:
                return resp.content
        except Exception as e:
            print(f"[OpenAI TTS Warning]: {e}")

    # 2. Resilient Multilingual TTS (No API key required)
    chunks = split_text_into_chunks(text, max_chars=140)
    if not chunks:
        return b""

    combined = bytearray()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for chunk in chunks:
        if not chunk.strip():
            continue
        try:
            encoded_query = requests.utils.quote(chunk.strip())
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_query}&tl={lang}&client=tw-ob"
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200 and res.content:
                combined.extend(res.content)
        except Exception as e:
            print(f"[TTS Chunk Warning]: {e}")

    return bytes(combined)
