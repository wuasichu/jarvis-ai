import sys
import time
import threading
import numpy as np
import pygame
import soundfile as sf
import tempfile
import os
from kokoro import KPipeline

_pipeline = None
_stop_flag = threading.Event()

pygame.mixer.init()

def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = KPipeline(lang_code='e')
    return _pipeline

def print_animated_message(message):
    for char in message:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.03)
    print()

def stop():
    _stop_flag.set()
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()

def Co_speak(text):
    _stop_flag.clear()
    tmp_path = None
    try:
        pipeline = _get_pipeline()
        chunks = list(pipeline(text, voice='ef_dora'))
        audio = np.concatenate([a for _, _, a in chunks])

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, 24000)
            tmp_path = f.name

        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if _stop_flag.is_set():
                pygame.mixer.music.stop()
                break
            time.sleep(0.05)

    except Exception as e:
        print(f"TTS error: {e}")
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

def speak(text):
    t1 = threading.Thread(target=Co_speak, args=(text,))
    t2 = threading.Thread(target=print_animated_message, args=(text,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
