# logging_config.py
import logging
from utils import generate_datetime_filename

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(generate_datetime_filename("split_video_maker", "log")),
            logging.StreamHandler()
        ]
    )
