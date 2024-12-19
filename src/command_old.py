''' Бибилотеки '''
import logging
import os
import yaml
import subprocess
import random
import threading
import psutil

''' Модули '''
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import jaccard_score
import numpy as np
from player import play_audio_response
from config_loader import load_config

CONFIG_PATH = '../config/config.json'

commands_path = '../commands'
logger = logging.getLogger("Jarvis")
config = load_config(CONFIG_PATH)

""" коэффициент Жаккара между двумя строками """
def jaccard_similarity(str1, str2):

    vectorizer = CountVectorizer().fit([str1, str2])
    vectors = vectorizer.transform([str1, str2]).toarray()
    return jaccard_score(vectors[0], vectors[1], average='binary')

# ======= Парсинг YAML-файлов =======
def parse_commands(commands_path):

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

# ======= Поиск подходящей команды =======

def find_command(user_input, commands, fuzzy_threshold=70, jaccard_threshold=0.3):

    """
    Ищет подходящую команду по фразе пользователя, используя коэффициент Жаккара и fuzzywuzzy.

    :param user_input: Ввод пользователя
    :param commands: Список доступных команд
    :param fuzzy_threshold: Минимальный процент совпадения для fuzzywuzzy
    :param jaccard_threshold: Минимальный коэффициент Жаккара
    :return: Подходящая команда или None
    """

    logger.info(f'Поиск команды для фразы: {user_input}')
    best_match = None
    best_score = 0

    for cmd in commands:
        for phrase in cmd.get('phrases', []):
            fuzzy_similarity = fuzz.partial_ratio(user_input.lower(), phrase.lower())

            jaccard_similarity_score = jaccard_similarity(user_input.lower(), phrase.lower())

            logger.info(
                f'Проверка фразы: "{phrase}" — Fuzzy: {fuzzy_similarity}%, '
                f'Jaccard: {jaccard_similarity_score:.2f}'
            )

            if fuzzy_similarity >= fuzzy_threshold and jaccard_similarity_score >= jaccard_threshold:
                combined_score = fuzzy_similarity * jaccard_similarity_score
                if combined_score > best_score:
                    best_match = cmd
                    best_score = combined_score

    if best_match:
        logger.info(f'Найдена команда: {best_match} с комбинированным баллом {best_score}')
        return best_match
    else:
        logger.warning('Команда не найдена.')
        return None

# ======= Выполнение команды =======

def validate_command(command):

    required_keys = ['command', 'voice', 'phrases']
    for key in required_keys:
        if key not in command:
            raise ValueError(f"Отсутствует ключ: {key}")
    if 'action' not in command['command']:
        raise ValueError("Отсутствует 'action' в команде")
    if 'sounds' not in command['voice']:
        raise ValueError("Отсутствуют 'sounds' в голосовых данных")

def handle_cli_command(cli_cmd, cli_args):
    logger.info(f"Выполняется команда: {cli_cmd} {cli_args}")
    subprocess.run([cli_cmd] + cli_args)

def play_sound(sounds):
    sound_directory = config['sound_directory']

    execute_sound = random.choice(sounds)
    logger.info(f'Выбран голосовой ответ: {execute_sound}')
    sound_path = f'{sound_directory}/{execute_sound}.wav'
    sound_thread = threading.Thread(target=play_audio_response, args=(sound_path,))
    sound_thread.start()
    return sound_thread

def is_process_running(process_name):

    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
    return False

def execute_command(command):

    try:
        validate_command(command)
        action = command['command']['action']
        if action == 'cli':
            cli_cmd = command['command']['cli_cmd']
            cli_args = command['command'].get('cli_args', [])
            sounds = command['voice']['sounds']

            if cli_cmd == 'taskkill':
                target_app = next((arg for arg in cli_args if arg.endswith(".exe")), None)

                if target_app:
                    if not is_process_running(target_app):
                        logger.warning(f"Приложение {target_app} не запущено.")
                        play_audio_response(file_path='../JarvisSound/appnotclose.wav')
                        return

            sound_thread = play_sound(sounds)
            handle_cli_command(cli_cmd, cli_args)

            sound_thread.join()
        else:
            logger.warning(f"Неизвестный тип команды: {action}")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды: {e}", exc_info=True)

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