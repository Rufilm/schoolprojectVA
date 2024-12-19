''' Бибилотеки '''
from typing import Any, List, Dict, Optional, Callable
from threading import Thread
from rapidfuzz import fuzz
from pathlib import Path
import subprocess
import threading
import logging
import random
import psutil
import winreg
import yaml
import os

''' Модули '''
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import jaccard_score
from player import play_audio_response
from config_loader import load_config
from fuzzywuzzy import fuzz
import numpy as np

CONFIG_PATH = '../config/config.json'
ACTION_HANDLERS = {}

commands_path = '../commands'
logger = logging.getLogger("Jarvis")
config = load_config(CONFIG_PATH)

# ======= Парсинг YAML-файлов =======
def parse_commands(commands_path: str) -> List[Dict[str, Any]]:

    '''
     Парсим YAML список команд по определенному пути

    :param commands_path: Путь до папки с файлами .yaml
    :return: Список команд или пустой список
     '''

    commands = []
    for root, dirs, files in os.walk(commands_path):
        for file in files:
            if file == 'command.yaml':
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        command_data = yaml.safe_load(f)
                        commands.extend(command_data['list'])
                    except Exception as e:
                        print(f"Ошибка при парсинге {file_path}: {e}")
    return commands

# ======= Коэффициент схожести для команд =======
def jaccard_similarity(str1: str, str2: str) -> float:
    vectorizer = CountVectorizer().fit([str1, str2])
    vectors = vectorizer.transform([str1, str2]).toarray()
    return jaccard_score(vectors[0], vectors[1], average='binary')

# ======= Поиск подходящей команды =======

def find_command(user_input: str, commands: List[Dict[str, Any]], fuzzy_threshold: int = 70, jaccard_threshold: float = 0.3) -> Optional[Dict[str, Any]]:

    """
    Ищет подходящую команду по фразе пользователя, используя коэффициент Жаккара и fuzzywuzzy.

    :param user_input: Ввод пользователя
    :param commands: Список доступных команд
    :param fuzzy_threshold: Минимальный процент совпадения для fuzzywuzzy
    :param jaccard_threshold: Минимальный коэффициент Жаккара
    :return: Подходящая команда или None
    """

    logger.info(f"Поиск команды для фразы: {user_input}")
    best_match = None
    best_score = 0

    for cmd in commands:
        for phrase in cmd.get('phrases', []):
            fuzzy_score = fuzz.partial_ratio(user_input, phrase)
            jaccard_score = jaccard_similarity(user_input, phrase)
            combined_score = fuzzy_score * jaccard_score

            if fuzzy_score >= fuzzy_threshold and jaccard_score >= jaccard_threshold and combined_score > best_score:
                best_match = cmd
                best_score = combined_score

    if best_match:
        logger.info(f"Найдена команда: {best_match} с баллом {best_score}")
    else:
        logger.warning("Команда не найдена.")
    return best_match

# ======= Выполнение команды =======

def register_action(action: str) -> Callable[[Callable], Callable]:
    """
    Декоратор для регистрации обработчиков действий.
    """
    def decorator(func: Callable) -> Callable:
        ACTION_HANDLERS[action] = func
        return func
    return decorator

def validate_command(command: Dict[str, Any]) -> None:

    required_keys = ['command', 'voice', 'phrases']
    for key in required_keys:
        if key not in command:
            raise ValueError(f"Отсутствует ключ: {key}")
    if 'action' not in command['command']:
        raise ValueError("Отсутствует 'action' в команде")
    if 'sounds' not in command['voice']:
        raise ValueError("Отсутствуют 'sounds' в голосовых данных")

def handle_cli_command(cli_cmd: str, cli_args: List[str]) -> None:
    logger.info(f"Выполняется команда: {cli_cmd} {cli_args}")
    subprocess.run([cli_cmd] + cli_args)

def play_sound(sounds: List[str]) -> None:
    """Воспроизводит случайный звуковой файл."""
    sound_directory = config['sound_directory']
    selected_sound = random.choice(sounds)
    sound_path = Path(f"{sound_directory}/{selected_sound}.wav")
    try:
        logger.info(f"Воспроизведение звука: {sound_path}")
        play_audio_response(str(sound_path))  # Преобразование в строку
    except Exception as e:
        logger.error(f"Ошибка при воспроизведении звука: {e}")

def is_process_running(process_name: str) -> bool:
    """Проверяет, запущен ли процесс с заданным именем."""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
    return False

# ======= Выполнение команды =======
def execute_command(command: Dict[str, Any]) -> None:
    try:
        action = command['command']['action']
        handler = ACTION_HANDLERS.get(action)
        if handler:
            handler(command)
        else:
            logger.warning(f"Неизвестный action: {action}")
    except Exception as e:
        logger.error(f"Ошибка выполнения команды: {e}", exc_info=True)


def handle_general_actions(command: Dict[str, Any]) -> None:

    action = command['command']['action']
    if action == "cli":
        handle_cli_action(command)
    elif action == "terminate":
        handle_terminate_action(command)
    elif action == "stop_chaining":
        handle_stop_chaining_action(command)
    else:
        logger.warning(f"Обработчик не найден для действия: {action}")
        raise ValueError(f"Обработчик отсутствует для action: {action}")


# === Обработчики ===
@register_action('voice')
def handle_voice_action(command: Dict[str, Any]) -> None:
    sounds = command.get('voice', {}).get('sounds', [])
    if not sounds:
        logger.warning("Список звуков пуст. Нечего воспроизводить.")
        return

    # Используем глобальную переменную config
    sound_directory = Path(config.get('sound_directory', "../JarvisSound"))
    sound_path = sound_directory / f"{random.choice(sounds)}.wav"

    if not sound_path.exists():
        logger.error(f"Файл {sound_path} не найден.")
        return

    try:
        logger.info(f"Воспроизведение звука: {sound_path}")
        play_audio_response(str(sound_path))  # Здесь передаём путь как строку
    except Exception as e:
        logger.error(f"Ошибка при воспроизведении звука: {e}")

def execute_exe(exe_path: str, exe_args: List[str]) -> bool:
    try:
        logger.info(f"Запуск исполняемого файла: {exe_path} с аргументами {exe_args}")
        subprocess.run([exe_path] + exe_args, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Execution failed: {e}")
        return False

@register_action('exe')
def handle_exe_command(command: Dict[str, Any]) -> None:
    try:

        base_dir = Path(__file__).resolve().parent.parent
        exe_path = base_dir / command['command']['exe_path']
        exe_args = command['command'].get('exe_args', [])
        sounds = command['voice']['sounds']

        if not exe_path.exists():
            logger.error(f"Исполняемый файл не найден: {exe_path}")
            return

        if execute_exe(str(exe_path), exe_args):
            logger.info("Исполняемый файл успешно запущен.")
            play_sound(sounds)
        else:
            logger.error("Ошибка при запуске исполняемого файла.")
    except Exception as e:
        logger.error(f"Ошибка в handle_exe_command: {e}")


@register_action('cli')
def handle_cli_action(command: Dict[str, Any]) -> None:
    cli_cmd = command['command']['cli_cmd']
    cli_args = command['command'].get('cli_args', [])
    sounds = command['voice']['sounds']

    if cli_cmd == 'taskkill':
        target_app = next((arg for arg in cli_args if arg.endswith(".exe")), None)
        if target_app and not is_process_running(target_app):
            logger.warning(f"Приложение {target_app} не запущено.")
            play_audio_response('../JarvisSound/appnotclose.wav')
            return

    sound_thread = Thread(target=play_sound, args=(sounds,))
    sound_thread.start()
    handle_cli_command(cli_cmd, cli_args)
    sound_thread.join()


''' Проверка исполнения '''

if __name__ == '__main__':

    print("Парсинг команд из YAML-файлов...")
    commands = parse_commands(commands_path)

    if not commands:
        print("Команды не найдены. Проверьте директорию с командами.")
        exit(1)

    print("Загруженные команды:")
    for idx, cmd in enumerate(commands, start=1):
        print(f"{idx}. {cmd.get('phrases', ['<Нет фраз>'])}")

    while True:
        user_input = input("\nВведите фразу (или 'exit' для выхода): ").strip()
        if user_input.lower() == 'exit':
            print("Выход из программы.")
            break

        matched_command = find_command(user_input, commands)
        if matched_command:
            print(f"Найдена команда: {matched_command['command']}")
            execute_command(matched_command)
        else:
            print("Команда не найдена. Попробуйте еще раз.")