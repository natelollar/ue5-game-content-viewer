import socket
import time
from pathlib import Path

import pygetwindow as gw


def focus_unreal_window():
    """Focus the Unreal Editor window to ensure full performance."""
    try:
        # find unreal editor window
        for window in gw.getAllTitles():
            if "Unreal Editor" in window or "Unreal" in window:
                unreal_window = gw.getWindowsWithTitle(window)[0]
                unreal_window.activate()
                print("Focused Unreal Editor window")
                return
        print("Unreal Editor window not found.")
    except Exception as e:
        print(f"Error focusing Unreal window: {e}")


def send(script_path: Path | str, host: str = "127.0.0.1", port: int = 7777) -> str:
    """Send script to Unreal over port.

    Args:
        script_path: File path to the Unreal Python script location.

    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(str(script_path).encode("utf-8"))
            response = s.recv(4096).decode("utf-8")
            print("Response from Unreal:\n", response)

            # attempt to focus the Unreal window after sending the script
            time.sleep(1)  # wait for Unreal to process the script
            focus_unreal_window()
            return response

    except Exception as e:
        print(f"Error: {e}")
        return f"{e}"
