
import logging
import sys

# Create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create stream handler and set level to debug
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)

# Add stream handler to logger
logger.addHandler(stream_handler)
