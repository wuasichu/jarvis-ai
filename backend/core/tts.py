import re
import asyncio
import tempfile
import os
import threading
import time
import edge_tts
import pygame

_VOICE = "es-ES-AlvaroNeural"
_MAX_CHARS = 400
_stop_event = threading.Event()

# Inicializar mixer en el hilo principal al importar el módulo
try:
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.init()
    print("[TTS] pygame.mixer inicializado OK")
except Exception as e:
    print(f"[TTS] ERROR init mixer: {e}")


def _clean_for_speech(text: str) -> str:
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.M)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.M)
    text = re.sub(r'\n+', ' ', text).strip()
    if len(text) > _MAX_CHARS:
        cut = text[:_MAX_CHARS].rsplit(' ', 1)[0]
        text = cut + '.'
    return text


async def speak_async(text: str):
    _stop_event.clear()
    text = _clean_for_speech(text)
    if not text:
        print("[TTS] Texto vacío, saltando")
        return

    print(f"[TTS] Generando audio: {text[:60]}...")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name

    try:
        communicate = edge_tts.Communicate(text, _VOICE)
        await communicate.save(tmp_path)
        size = os.path.getsize(tmp_path)
        print(f"[TTS] MP3 guardado: {size} bytes en {tmp_path}")

        if _stop_event.is_set():
            print("[TTS] Interrumpido antes de reproducir")
            return

        print("[TTS] Iniciando reproducción...")
        await asyncio.to_thread(_play_blocking, tmp_path)
        print("[TTS] Reproducción completada")

    except Exception as e:
        import traceback
        print(f"[TTS] ERROR: {e}")
        traceback.print_exc()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _play_blocking(path: str):
    try:
        if not pygame.mixer.get_init():
            print("[TTS] Mixer no inicializado, reiniciando...")
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()

        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        print("[TTS] Reproduciendo...")

        while pygame.mixer.music.get_busy():
            if _stop_event.is_set():
                pygame.mixer.music.stop()
                print("[TTS] Parado por stop_event")
                break
            time.sleep(0.05)

    except Exception as e:
        import traceback
        print(f"[TTS] ERROR en playback: {e}")
        traceback.print_exc()


def stop_tts():
    _stop_event.set()
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass
