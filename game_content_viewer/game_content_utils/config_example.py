"""Example of using config_file.py"""
import config_file

## -- Use if launching file through Unreal port. -- ##
# from pathlib import Path
# import imp
# file_path = (Path(__file__).parent / "config_file.py").as_posix()
# config_file = imp.load_source('config_file', file_path)

# save file defaults
JSON_SAVE_FILE = config_file.JSON_SAVE_FILE
UE_FOLDER_PATH_KEY = config_file.UE_FOLDER_PATH_KEY
UE_FOLDER_PATH_VALUE = config_file.load_saver()
# database defaults
TABLE_NAME = config_file.TABLE_NAME
DB_FILE_PATH = config_file.DB_FILE_PATH

if __name__ == "__main__":
    print(JSON_SAVE_FILE)
    print(UE_FOLDER_PATH_KEY)
    print(UE_FOLDER_PATH_VALUE)

    print(TABLE_NAME)
    print(DB_FILE_PATH)
