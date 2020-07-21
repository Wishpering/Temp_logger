from logging import StreamHandler, getLogger, Formatter, INFO
from sys import stdout

class Logger:
    format = Formatter("%(asctime)s — %(levelname)s — %(message)s")

    @classmethod
    def get(cls):
        console_handler = StreamHandler(stdout)
        console_handler.setFormatter(Logger.format)
        
        logger = getLogger('temp_logger')
        logger.addHandler(console_handler)
        logger.setLevel(INFO)

        return logger
        