"""Entry point for the UE5 Game Content Viewer tool."""

import sys
from pathlib import Path

if __name__ == "__main__":
    # add root folder to system path if missing
    new_path = (Path(__file__).parent).as_posix()
    if new_path not in sys.path:
        sys.path.append(new_path)
        print(f"Appended to system path:{new_path}")

    from game_content_viewer import game_content_viewer_main
    # launch ui window
    game_content_viewer_main.main()