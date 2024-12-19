''' Библиотеки '''
import logging
from datetime import datetime
import time
import struct
import gc
import pyaudio
from setuptools.dist import assert_string_list
import os

''' Модули '''
from resource_manager import managed_porcupine, managed_stream
from player import play_random_hello
from recognizer import recognize_command_vosk
from config_loader import load_config
from until import filter_command
from command import parse_commands, find_command, execute_command
from logger_config import setup_logger

CONFIG_PATH = '../config/config.json'
logger = setup_logger()

def main():
    try:
        config = load_config(CONFIG_PATH)
        vosk_model_path = config['vosk_model_path']
        hello_phrases_path = config['hello_phrases_path']
        keywords_path = [config['keywords_path']]
        ACCESS_KEY = config['access_key']
        ASSISTANT_PHRASES_TBR = config['assistant_tbr_phrases']

        commands = parse_commands(config['commands_path'])
        logger.info("Команды загружены.")
        logger.info(f"Загруженные команды: {commands}")

        last_wake_time = 0
        logger.info("Голосовой ассистент запущен...")

        with managed_porcupine(access_key=ACCESS_KEY, keyword_paths=keywords_path) as porcupine:
            pa = pyaudio.PyAudio()
            with managed_stream(pa, rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
                                input=True, frames_per_buffer=porcupine.frame_length) as audio_stream:

                while True:
                    try:
                        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                        if porcupine.process(pcm) >= 0:
                            current_time = time.time()
                            if current_time - last_wake_time > 2:
                                last_wake_time = current_time
                                play_random_hello(hello_phrases_path)

                                raw_command = recognize_command_vosk(vosk_model_path)
                                if raw_command is None:
                                    logger.info("Отсутствует полученная фраза")
                                    continue

                                logger.info(f"Получена фраза: {raw_command}")

                                filtered_command = filter_command(raw_command, ASSISTANT_PHRASES_TBR)
                                if not filtered_command:
                                    logger.info("Фраза пуста после фильтрации. Возврат в режим ожидания...")
                                    continue

                                logger.info(f"Команда отфильтрована: {filtered_command}")
                                cmd = find_command(filtered_command, commands)

                                if cmd:
                                    logger.info(f"Выполнение команды: {cmd}")
                                    execute_command(cmd)
                                else:
                                    logger.warning("Команда не найдена.")

                    except Exception as e:
                        logger.error(f"Ошибка в основном цикле: {e}", exc_info=True)

    except FileNotFoundError as e:
        logger.critical(f"Файл конфигурации не найден: {e}")
    except KeyboardInterrupt:
        logger.info("Ассистент остановлен пользователем.")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        gc.collect()
        logger.info("Очистка памяти завершена.")


if __name__ == '__main__':
    main()
