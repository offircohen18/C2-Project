import socket
import threading
import uuid
import time
import os
from dotenv import load_dotenv

from crypto_utils import encrypt_message, decrypt_message

load_dotenv()

HOST = os.getenv("SERVER_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVER_PORT", 9000))
HEARTBEAT_TIMEOUT = 15  # שניות

clients = {}      # client_id -> {conn, addr, last_seen}
clients_lock = threading.Lock()


# -----------------------------
# Message Protocol
# -----------------------------
def send_msg(conn, obj):
    cipher = encrypt_message(obj)
    conn.sendall(len(cipher).to_bytes(4, "big") + cipher)


def recv_msg(conn):
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
    except:
        return None


# -----------------------------
# Client Handler Thread
# -----------------------------
def client_handler(conn, addr, client_id):
    print(f"[+] Client connected: {client_id} from {addr}")

    with conn:
        while True:
            try:
                msg = recv_msg(conn)
                if msg is None:
                    break

                typ = msg.get("type")

                if typ == "response":
                    print(f"[Response] {client_id}: {msg.get('result')[:1000]}")  # מוגבל ל-1000 תווים

                elif typ == "heartbeat":
                    with clients_lock:
                        if client_id in clients:
                            clients[client_id]["last_seen"] = time.time()

                else:
                    print(f"[{client_id}] Unknown message: {msg}")

            except Exception as e:
                print(f"[!] Error with client {client_id}: {e}")
                break

    with clients_lock:
        clients.pop(client_id, None)

    print(f"[-] Client disconnected: {client_id}")


# -----------------------------
# Accept Thread
# -----------------------------
def accept_loop(sock):
    while True:
        conn, addr = sock.accept()
        cid = str(uuid.uuid4())[:8]
        thread = threading.Thread(
            target=client_handler, args=(conn, addr, cid), daemon=True
        )
        with clients_lock:
            clients[cid] = {"conn": conn, "addr": addr, "last_seen": time.time()}
        thread.start()


# -----------------------------
# Send Command Async
# -----------------------------
def send_command_async(cid, command):
    with clients_lock:
        info = clients.get(cid)
    if not info:
        print("No such client")
        return
    try:
        send_msg(info["conn"], {"type": "command", "cmd": command})
        print(f"Sent to {cid}")
    except Exception as e:
        print("Send error:", e)


# -----------------------------
# Admin CLI
# -----------------------------
def admin_cli():
    print("Admin CLI ready. Type 'help'.")
    help_text = """
Commands:
  list
  send <id> <command>
  kill <id>
  help
  quit
"""

    while True:
        cmdline = input("> ").strip()
        if not cmdline:
            continue

        parts = cmdline.split(" ", 2)
        cmd = parts[0].lower()

        if cmd == "help":
            print(help_text)

        elif cmd == "list":
            now = time.time()
            with clients_lock:
                if not clients:
                    print("(no clients connected)")
                for cid, info in clients.items():
                    age = now - info["last_seen"]
                    status = "alive" if age <= HEARTBEAT_TIMEOUT else "timeout"
                    print(f"{cid}\t{info['addr']}\tlast_seen={age:.1f}s\t{status}")

        elif cmd == "send" and len(parts) >= 3:
            cid = parts[1]
            command = parts[2]
            threading.Thread(target=send_command_async, args=(cid, command), daemon=True).start()

        elif cmd == "kill" and len(parts) >= 2:
            cid = parts[1]
            with clients_lock:
                info = clients.get(cid)
            if not info:
                print("No such client")
                continue
            info["conn"].close()
            print("Client closed.")

        elif cmd == "quit":
            print("Exiting server.")
            break

        else:
            print("Unknown command. Type 'help'.")


# -----------------------------
# Main
# -----------------------------
def main():
    print("Starting server...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)

    print(f"Listening on {HOST}:{PORT}")

    threading.Thread(target=accept_loop, args=(s,), daemon=True).start()
    admin_cli()
    s.close()


if __name__ == "__main__":
    main()
