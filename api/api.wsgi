#!/usr/bin/python
import sys
import os
import logging
import logging.handlers
# logging.basicConfig(stream=sys.stderr)
basedir = os.path.abspath(os.path.dirname(__file__))
i_log = os.path.join(basedir, "logs", "api_info.log")
rh = logging.handlers.RotatingFileHandler(
    filename=i_log,
    mode='a',
    maxBytes=(5 * 1024 * 1024),
    backupCount=2,
    encoding=None,
    delay=0)
logging.basicConfig(handlers=[rh],
                    level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s - (%(lineno)d): %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')


sys.path.insert(0, "/var/www/html/api")
from api import app as application
