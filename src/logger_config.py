import logging
from datetime import datetime

def setup_logger():

    log_filename = datetime.now().strftime("../logs/Jarvis_%Y-%m-%d_%H-%M-%S.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(module)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_filename, mode='a', encoding='utf-8')
        ]
    )

    return logging.getLogger("Jarvis")
