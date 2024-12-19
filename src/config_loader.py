import os
import json
import logging

def load_config(path):
    """Загружает файл конфигурации и проверяет наличие ключей."""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            config = json.load(file)
            required_keys = ['vosk_model_path', 'hello_phrases_path', 'keywords_path', 'access_key', 'assistant_tbr_phrases']
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                raise ValueError(f"Отсутствует(-ют) ключ(-и): {missing_keys}")
            return config
    else:
        raise FileNotFoundError(f"Файл конфигурации {path} не найден.")
