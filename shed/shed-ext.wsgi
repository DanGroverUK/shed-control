#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)

sys.path.insert(0, "/var/www/html/shed-ext")
from shed import app as application
