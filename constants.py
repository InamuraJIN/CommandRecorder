import os
import pathlib

here_directory = os.path.dirname(__file__)

STORAGE_DIR = here_directory + "/Storage"
STORAGE_MACROS_DIR = f"{STORAGE_DIR}/macros"

SETTINGS_JSON_PATH = f"{STORAGE_DIR}/settings.json"
INTERFACE_DATA_JSON_PATH = f"{STORAGE_DIR}/interface_data.json"

COMMAND_FILENAME_PREFIX = "__COMMANDRECORDER__"