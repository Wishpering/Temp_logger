#!/usr/bin/python3

import logging
from datetime import datetime

class Logger(object):
    def __init__(self, Path, log_Name):
        logging.basicConfig(filename = Path + "/logs/" + log_Name, level = logging.ERROR)
        self.log = logging.getLogger("DHT")
        
    def write_To_Log(self, data):
        self.log.exception(str(datetime.now()) + " " + data + "\n")
                                                                            
