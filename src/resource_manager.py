import logging
import pvporcupine
from contextlib import contextmanager

logger = logging.getLogger('Jarvis')

@contextmanager
def managed_stream(pa, **kwargs):
    stream = pa.open(**kwargs)
    try:
        yield stream
    finally:
        stream.stop_stream()
        stream.close()
        logger.info("Аудиопоток освобождён.")

@contextmanager
def managed_porcupine(access_key, keyword_paths):
    porcupine = pvporcupine.create(access_key=access_key, keyword_paths=keyword_paths)
    try:
        yield porcupine
    finally:
        porcupine.delete()
        logger.info("Porcupine освобождён.")
