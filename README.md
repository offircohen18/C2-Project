# C2 Server & Client - Python

## Overview
This project is a demonstration of a Command & Control (C2) server with a client implementation.  
It supports multiple clients, encrypted communication, asynchronous command execution, and heartbeat monitoring.

---

## Architecture
- **Server**  
  - Accepts multiple concurrent client connections  
  - Provides a CLI for the admin to interact with clients  
  - Sends commands asynchronously  
  - Tracks client heartbeats and connection status  

- **Client**  
  - Connects automatically to the configured server  
  - Receives commands, executes them, and returns output  
  - Sends periodic heartbeat messages  
  - Handles commands asynchronously using an internal queue  

- **Encryption**  
  - All communication is encrypted using `Fernet` (AES‑128 + HMAC)  
  - Secret key is loaded from `.env` (not hardcoded)  

---

## Requirements

- Python 3.8+
- Dependencies:

```bash
pip install cryptography python-dotenv
```

## Setup & Running

1. Start the server:
```bash
 python server.py
```

2. Start the Client:
```bash
 python client.py
```

## Server CLI Commands

`list` – Display all connected clients and their heartbeat status

`send <id> <command>` – Send a command to a client (HELLO, ECHO <text>, or system commands)

`kill <id>` – Disconnect a client

`help` – Display available commands

`quit` – Exit the server

### Notes

- HELLO and ECHO commands are handled internally and do not require OS support


- Other commands are executed via subprocess


- Heartbeat ensures clients are alive and updates status in the server CLI
