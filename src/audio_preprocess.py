import numpy as np
import noisereduce as nr

def preprocess_audio(audio_data):
    """Подавляет шумы из аудиопотока."""
    audio_np = np.frombuffer(audio_data, dtype=np.int16)
    reduced_noise = nr.reduce_noise(y=audio_np, sr=16000)
    return reduced_noise.tobytes()
