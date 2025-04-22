"""Test sending a script to Unreal engine."""

from pathlib import Path

import send_to_unreal_port

script_path = Path(__file__).parents[1] / "unreal_scripts" / "game_content_scanner.py"

if __name__ == "__main__":
    send_to_unreal_port.send(script_path)
