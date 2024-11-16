import os
import time
from datetime import datetime, timedelta
import threading
import logging

logger = logging.getLogger(__name__)


class DirectoryCleaner:
    def __init__(self, directories, age_limit_days=2, check_interval_seconds=3600):
        """
        Initialize the DirectoryCleaner.

        :param directories: List of directories to monitor.
        :param age_limit_days: Age limit in days to determine when to delete files or directories.
        :param check_interval_seconds: Time interval (in seconds) between directory checks.
        """
        self.directories = directories
        self.age_limit = timedelta(days=age_limit_days)
        self.check_interval = check_interval_seconds
        self.running = False
        self.thread = None

    def start(self):
        """
        Start the directory cleaner in a separate thread.
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info("DirectoryCleaner started.")

    def stop(self):
        """
        Stop the directory cleaner.
        """
        if self.running:
            self.running = False
            self.thread.join()
            logger.info("DirectoryCleaner stopped.")

    def _run(self):
        """
        Internal method to periodically clean directories.
        """
        while self.running:
            logger.info(f"Starting cleanup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.clean()
            time.sleep(self.check_interval)

    def clean(self):
        """
        Iterate through the directories and delete files and subdirectories older than the age limit.
        """
        now = datetime.now()
        for directory in self.directories:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory, topdown=False):
                    # Check and remove files
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._is_older_than(file_path, now):
                            os.remove(file_path)
                            logger.info(f"Deleted file: {file_path}")

                    # Check and remove empty directories
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        if self._is_older_than(dir_path, now) and not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            logger.info(f"Deleted directory: {dir_path}")

    def _is_older_than(self, path, current_time):
        """
        Check if the given file or directory is older than the age limit.

        :param path: Path to the file or directory.
        :param current_time: The current time to compare against.
        :return: True if the file/directory is older than the age limit, False otherwise.
        """
        creation_time = datetime.fromtimestamp(os.path.getmtime(path))
        return (current_time - creation_time) > self.age_limit
