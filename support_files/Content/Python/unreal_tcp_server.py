"""A TCP server for executing Python scripts and commands in Unreal Engine.

This script runs a TCP server within Unreal Engine, listening for commands from clients (ex. Python
script paths or direct commands) and executing them.
"""

import os
import socket
import threading
import time
import traceback

import unreal


class TCPServer:
    """A TCP server for executing Python scripts and commands in Unreal."""

    def __init__(self, host: str = "0.0.0.0", port: int = 7777) -> None:
        """Initializes the TCP server with the specified host and port.

        Args:
            host: The host address to bind the server.
            port: The port to listen on.

        """
        self.host = host
        self.port = port
        self.server_running = True
        self.server_socket = None
        self.main_thread_queue = []  # queue for main thread tasks
        self.tick_handle = unreal.register_slate_post_tick_callback(self._tick)

    def _tick(self, delta_time: float) -> None:
        """Process queued tasks on the main thread.

        Args:
            delta_time: Time since the last tick, provided by Unreal.

        """
        while self.main_thread_queue:
            script_path = self.main_thread_queue.pop(0)
            try:
                unreal.log(f"Executing on main thread: {script_path}")
                unreal.PythonScriptLibrary.execute_python_command_ex(
                    script_path,
                    execution_mode=unreal.PythonCommandExecutionMode.EXECUTE_FILE,
                    file_execution_scope=unreal.PythonFileExecutionScope.PUBLIC,
                )
            except Exception:
                unreal.log(f"Main thread error: {traceback.format_exc()}")

    def execute_script(self, script_path: str, client_socket: socket.socket) -> bytes:
        """Executes a Python script or command received from a client.

        If the input is a valid `.py` file path, queues it for main thread execution.
            Otherwise, attempts to execute the input as a Python command using `exec`.

        Args:
            script_path: The script path or command received from the client.
            client_socket: The client socket for sending responses.

        Returns:
            A byte string with the execution result or error message.

        """
        command = script_path.strip()
        if os.path.isfile(command) and command.endswith(".py"):
            # queue script execution on main thread
            self.main_thread_queue.append(command)
            return b"Script queued for execution"
        try:
            exec(command, globals())
            return b"Command executed successfully"
        except Exception:
            error_msg = f"Error executing: {command}\n{traceback.format_exc()}"
            print(error_msg)
            return error_msg.encode("utf-8")

    def start(self) -> None:
        """Starts the TCP server to listen for client connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[UE5 TCP] Server started on {self.host}:{self.port}")

        while self.server_running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"[UE5 TCP] Connection from {addr}")
                data = client_socket.recv(1024).decode().strip()
                print(f"[UE5 TCP] Received: {data}")

                if data == "STOP":
                    self.server_running = False
                    client_socket.sendall(b"Server shutting down...")
                    client_socket.close()
                    break
                if data == "RESTART":
                    client_socket.sendall(b"Server restarting...")
                    client_socket.close()
                    self.restart()
                    return
                response = self.execute_script(data, client_socket)
                client_socket.sendall(response)
                client_socket.close()
            except Exception as e:
                print(f"[UE5 TCP] Error: {e}")
        self.server_socket.close()
        print("[UE5 TCP] Server socket closed.")

    def restart(self):
        """Restarts the TCP server by stopping and starting it again."""
        self.stop()
        time.sleep(1)
        self.start()

    def stop(self) -> None:
        """Stops the TCP server and cleans up resources."""
        self.server_running = False
        if self.server_socket:
            self.server_socket.close()
        unreal.unregister_slate_post_tick_callback(self.tick_handle)
        print("[UE5 TCP] Server stopped.")


# run tcp server
def main() -> None:
    """Starts the TCP server in a background thread."""
    tcp_server = TCPServer(port=7777)
    server_thread = threading.Thread(target=tcp_server.start, daemon=True)
    server_thread.start()
    print("[UE5 TCP] Server running in background thread")
