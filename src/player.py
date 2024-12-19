import wave
import os
import random
import logging
import pyaudio
from typing import Optional
from resource_manager import managed_stream

logger = logging.getLogger("Jarvis")

# Параметризация размера буфера
BUFFER_SIZE = 1024


def play_audio_response(file_path: Optional[str] = None, directory_path: Optional[str] = None) -> None:
    """
    Воспроизводит аудио из указанного файла или случайного файла в директории.

    :param file_path: Путь к файлу для воспроизведения.
    :param directory_path: Путь к директории с .wav файлами.
    """
    if not file_path and not directory_path:
        logger.error("Не указаны ни файл, ни директория для воспроизведения.")
        return

    try:
        if directory_path:
            wav_files = [file for file in os.listdir(directory_path) if file.endswith('.wav')]
            if not wav_files:
                logger.error(f"В директории {directory_path} нет .wav файлов.")
                return
            file_path = os.path.join(directory_path, random.choice(wav_files))

        if not file_path or not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            return

        logger.info(f"Начато воспроизведение файла: {file_path}")

        with wave.open(file_path, 'rb') as wf:
            pa = pyaudio.PyAudio()
            try:
                with managed_stream(pa,
                                    format=pa.get_format_from_width(wf.getsampwidth()),
                                    channels=wf.getnchannels(),
                                    rate=wf.getframerate(),
                                    output=True) as stream:
                    data = wf.readframes(BUFFER_SIZE)
                    while data:
                        stream.write(data)
                        data = wf.readframes(BUFFER_SIZE)

                logger.info(f"Файл успешно воспроизведён: {file_path}")

            finally:
                pa.terminate()

    except wave.Error as e:
        logger.error(f"Ошибка чтения WAV файла: {file_path}: {e}")
    except OSError as e:
        logger.error(f"Ошибка воспроизведения файла {file_path}: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}", exc_info=True)


def play_random_hello(hello_phrases_path: str) -> None:
    """
    Воспроизводит случайное приветствие из указанной директории.

    :param hello_phrases_path: Путь к директории с приветствиями.
    """
    logger.info("Воспроизведение случайного приветствия...")
    play_audio_response(directory_path=hello_phrases_path)