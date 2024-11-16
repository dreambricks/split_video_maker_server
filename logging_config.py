# logging_config.py
import logging
from utils import generate_datetime_filename
import os


def setup_logging():
    os.makedirs("log", exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join("log", generate_datetime_filename("split_video_maker", "log"))),
            logging.StreamHandler()
        ]
    )
