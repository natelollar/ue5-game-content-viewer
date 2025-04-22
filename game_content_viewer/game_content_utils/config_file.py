"""Config module holding variables for the Game Content Viewer application."""

import json
from pathlib import Path

# file paths
SCANNER_SCRIPT = Path(__file__).parents[1] / "unreal_scripts" / "game_content_scanner.py"
SUMMARY_SCRIPT = Path(__file__).parents[1] / "unreal_scripts" / "game_content_summary.py"
REFRESH_THUMBNAILS_SCRIPT = (
    Path(__file__).parents[1] / "unreal_scripts" / "game_content_thumbnails.py"
)
WNDW_ICON_PATH = (Path(__file__).parents[1] / "data" / "icons" / "menubar_icon_128.jpg").as_posix()
LAUNCH_UE_SCRIPT = (Path(__file__).parents[2] / "launch_ue.cmd").as_posix()

# save defaults
JSON_SAVE_FILE = (Path(__file__).parents[1] / "data" / "save_file.json").as_posix()
THUMBNAILS_SAVE_FOLDER = Path(__file__).parents[1] / "data" / "thumbnails"
DATA_FOLDER_PATH = Path(__file__).parents[1] / "data"

# database defaults
TABLE_NAME = "game_content"
SUMMARY_TABLE_NAME = "content_summary"
DB_FILE_PATH = Path(__file__).parents[1] / "data" / f"{TABLE_NAME}.db"
UE_FOLDER_PATH_KEY = "ue_folder_path"


def load_saver() -> str:
    """Load dictionary from save_file.json and return values."""
    try:
        with open(JSON_SAVE_FILE) as f:
            json_dict = json.load(f)
        UE_FOLDER_PATH_VALUE = json_dict[UE_FOLDER_PATH_KEY]
    except (FileNotFoundError, json.JSONDecodeError):
        UE_FOLDER_PATH_VALUE = "/Game/"

    return UE_FOLDER_PATH_VALUE
