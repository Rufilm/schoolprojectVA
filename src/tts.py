import asyncio
import edge_tts
from pydub import AudioSegment
import numpy as np
from scipy.io.wavfile import write
import os

# Генерация аудио в формате MP3
async def generate_audio(text, output_file):
    communicate = edge_tts.Communicate(text=text, voice="ru-RU-DmitryNeural", rate="+20%")
    await communicate.save(output_file)

# Конвертация из MP3 в WAV
def convert_to_wav(input_file, output_file):
    audio = AudioSegment.from_file(input_file, format="mp3")
    audio = audio.set_frame_rate(44100).set_channels(1).set_sample_width(2)
    audio.export(output_file, format="wav")

# Применение эффекта Flanger
def apply_flanger(input_file, output_file):
    audio = AudioSegment.from_wav(input_file)
    data = np.array(audio.get_array_of_samples()).astype(np.float32)
    rate = audio.frame_rate

    # Параметры Flanger
    depth = 0.002  # Максимальная задержка в секундах
    rate_hz = 0.25  # Частота модуляции
    max_delay_samples = int(depth * rate)
    modulation = (np.sin(2 * np.pi * np.arange(len(data)) * rate_hz / rate) + 1) / 2

    # Применение Flanger
    flanged_data = np.zeros_like(data, dtype=np.float32)
    for n in range(len(data)):
        delay = int(modulation[n] * max_delay_samples)
        if n - delay >= 0:
            flanged_data[n] = (data[n] + data[n - delay]) / 2

    # Сохранение результата
    write(output_file, rate, flanged_data.astype(np.int16))

# Основная функция
async def main():
    text = "Привет, я твой ассистент!"
    tts_file = "output_generated.mp3"  # Генерируем в MP3
    wav_file = "output_generated.wav"  # Конвертируем в WAV
    flanger_file = "output_flanger.wav"

    # Генерация MP3 и конвертация в WAV
    await generate_audio(text, tts_file)
    convert_to_wav(tts_file, wav_file)

    # Применение эффекта Flanger
    apply_flanger(wav_file, flanger_file)

    # Удаляем временные файлы
    if os.path.exists(tts_file):
        os.remove(tts_file)
        print(f"Удалён временный файл: {tts_file}")
    if os.path.exists(wav_file):
        os.remove(wav_file)
        print(f"Удалён временный файл: {wav_file}")

    print("Flanger эффект применён успешно!")

# Запуск
asyncio.run(main())
