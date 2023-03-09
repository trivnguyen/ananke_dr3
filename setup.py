
import shutil
from setuptools import setup

shutil.copy("config.ini", "src/ananke/config.ini")
setup()
