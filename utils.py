from datetime import datetime
import time
import logging
import random
import string

logger = logging.getLogger(__name__)


def generate_datetime_filename(prefix="file", extension="txt"):
    # Format the current date and time
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Construct the filename
    filename = f"{prefix}_{current_time}.{extension}"
    return filename


# timer decorator
# use like this:
# 
# @timer
# def some_function():
#     time.sleep(2)
def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper


def generate_random_string(length):
    if length <= 0:
        raise ValueError("Length must be a positive integer.")

    # Define characters safe for filenames and URLs
    allowed_chars = string.ascii_letters + string.digits + "-_"

    # Generate a random string
    random_string = ''.join(random.choices(allowed_chars, k=length))
    return random_string
