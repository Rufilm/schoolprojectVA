''' Библиотеки '''
import os
import json
import pyaudio
import logging

''' Модули '''
from vosk import Model, KaldiRecognizer
from resource_manager import managed_stream
from audio_preprocess import preprocess_audio

logger = logging.getLogger('Jarvis')

def recognize_command_vosk(vosk_model_path):
    """Распознаёт голосовую команду с использованием Vosk."""
    if not os.path.exists(vosk_model_path):
        logger.error("Модель Vosk не найдена.")
        return None

    model = Model(vosk_model_path)
    recognizer = KaldiRecognizer(model, 16000)

    pa = pyaudio.PyAudio()
    with managed_stream(pa, format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096) as stream:
        logger.info("Запись команды...")
        silent_frames = 0
        max_silent_frames = 10

        while True:
            data = stream.read(4096, exception_on_overflow=False)
            data = preprocess_audio(data)

            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                command = json.loads(result).get("text", "").strip()

                if command:
                    logger.info(f"Распознанная команда: {command}")
                    return command
                else:
                    logger.info("Распознан пустой ввод. Возврат в режим ожидания.")
                    return None

            silent_frames += 1
            if silent_frames >= max_silent_frames:
                logger.info("Не обнаружен голос пользователя")
                return None