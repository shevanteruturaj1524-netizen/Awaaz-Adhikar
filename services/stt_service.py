import os
import wave
from pathlib import Path
from typing import Optional
import requests
from config import BASE_DIR

LANGUAGE_LOCALES = {
    "hi": "hi-IN",
    "mr": "mr-IN",
    "bn": "bn-IN",
    "en": "en-IN",
    "te": "te-IN",
    "ta": "ta-IN",
    "gu": "gu-IN"
}

def transcribe_audio_file(file_path: Path, language: str = "hi") -> str:
    """
    Transcribes a real recorded audio file (WAV format preferred).
    Uses configured cloud provider (Groq/OpenAI) if API key exists in .env/environment,
    or falls back to high-resilience Google Speech Recognition via speech_recognition.
    Returns clean transcript string.
    """
    if not file_path.exists() or file_path.stat().st_size < 100:
        return ""

    locale = LANGUAGE_LOCALES.get(language, "hi-IN")
    groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    openai_api_key = (os.getenv("OPENAI_API_KEY") or "").strip()

    # 1. Groq Whisper (Ultra-fast cloud STT if key configured)
    if groq_api_key:
        try:
            with open(file_path, "rb") as f:
                resp = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {groq_api_key}"},
                    files={"file": (file_path.name, f, "audio/wav")},
                    data={
                        "model": "whisper-large-v3",
                        "language": language if language in ["hi", "mr", "bn", "en"] else "en",
                        "response_format": "json"
                    },
                    timeout=15
                )
            if resp.status_code == 200:
                transcript = resp.json().get("text", "").strip()
                if transcript:
                    return transcript
        except Exception as e:
            print(f"[Groq STT Warning]: {e}")

    # 2. OpenAI Whisper (Standard cloud STT if key configured)
    if openai_api_key:
        try:
            with open(file_path, "rb") as f:
                resp = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {openai_api_key}"},
                    files={"file": (file_path.name, f, "audio/wav")},
                    data={
                        "model": "whisper-1",
                        "language": language if language in ["hi", "mr", "bn", "en"] else "en",
                        "response_format": "json"
                    },
                    timeout=15
                )
            if resp.status_code == 200:
                transcript = resp.json().get("text", "").strip()
                if transcript:
                    return transcript
        except Exception as e:
            print(f"[OpenAI STT Warning]: {e}")

    # 3. Native SpeechRecognition with Google Speech API (No API key required)
    converted_tmp = None
    try:
        import speech_recognition as sr
        target_path = file_path

        # If audio is WebM/OGG/MP4 or non-WAV, convert to 16kHz mono WAV using ffmpeg
        if file_path.suffix.lower() != ".wav":
            try:
                import subprocess, imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                converted_tmp = file_path.with_suffix(".pcm.wav")
                cmd = [
                    ffmpeg_exe, "-y", "-i", str(file_path),
                    "-ar", "16000", "-ac", "1", "-f", "wav", str(converted_tmp)
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=8)
                if converted_tmp.exists() and converted_tmp.stat().st_size > 44:
                    target_path = converted_tmp
            except Exception as conv_err:
                print(f"[FFmpeg conversion notice]: {conv_err}")

        r = sr.Recognizer()
        r.energy_threshold = 250
        r.dynamic_energy_threshold = True

        with sr.AudioFile(str(target_path)) as source:
            audio_data = r.record(source)

        transcript = r.recognize_google(audio_data, language=locale)
        if transcript and isinstance(transcript, str):
            return transcript.strip()
    except sr.UnknownValueError:
        # Normal for silence / unvoiced audio
        return ""
    except Exception as e:
        print(f"[Backend STT Warning]: {type(e).__name__}: {e}")
        return ""
    finally:
        if converted_tmp and converted_tmp.exists():
            try:
                converted_tmp.unlink()
            except Exception:
                pass

    return ""
