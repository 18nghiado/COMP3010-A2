import socket
import select
import json
import os
import sys

CHAT_HISTORY_FILE = 'chat_history.txt'
MAX_HISTORY = 100

clients = {}
inputs = []

def save_message_to_file(message):
    with open(CHAT_HISTORY_FILE, 'a') as file:
        file.write(message + '\n')

def load_recent_messages():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r') as file:
            return file.readlines()[-MAX_HISTORY:]
    return []

def send_message(client_socket, message):
    try:
        client_socket.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f"Error sending message: {e}")

def broadcast_message(message, exclude_socket=None):
    for client_socket in clients.values():
        if client_socket != exclude_socket:
            send_message(client_socket, message)

def handle_new_connection(server_socket):
    client_socket, client_address = server_socket.accept()

    try:
        username = client_socket.recv(1024).decode('utf-8').strip()
        if username.startswith('{'):
            # Assume this is a web server request
            handle_web_request(client_socket, username)
            return
        if username in clients:
            send_message(client_socket, "Username already in use. Connection refused.")
            client_socket.close()
            print(f"Connection refused for {username} (already in use).")
            return

        clients[username] = client_socket
        inputs.append(client_socket)
        
        # Send recent chat history
        recent_messages = load_recent_messages()
        if recent_messages:
            send_message(client_socket, "Recent chat history:\n" + ''.join(recent_messages))
        
        print(f"{username} has joined the chat.")
        broadcast_message(f"{username} has joined the chat.", exclude_socket=client_socket)
    except Exception as e:
        print(f"Error handling new connection: {e}")

def handle_client_message(client_socket):
    try:
        message = client_socket.recv(1024).decode('utf-8')
        if message:
            if message.endswith("has left the chat."):
                handle_disconnect(client_socket)
            else:
                save_message_to_file(message)
                broadcast_message(message, exclude_socket=client_socket)
        else:
            handle_disconnect(client_socket)
    except Exception:
        handle_disconnect(client_socket)

def handle_disconnect(client_socket):
    for username, sock in clients.items():
        if sock == client_socket:
            print(f"{username} has left the chat.")
            inputs.remove(client_socket)
            del clients[username]
            client_socket.close()
            broadcast_message(f"{username} has left the chat.")
            break

def handle_web_request(client_socket, request):
    try:
        data = json.loads(request)
        
        # Check for both 'username' and 'text' keys in the JSON data
        if 'username' in data and 'text' in data:
            username = data['username']
            text = data['text']
            message = f"{username}: {text}"
            save_message_to_file(message)
            broadcast_message(message)
            response = {'status': 'Message received'}
            client_socket.sendall(json.dumps(response).encode('utf-8'))
        elif 'get_messages' in data:
            # Send recent messages
            messages = load_recent_messages()
            response = {'messages': [{'username': msg.split(':')[0], 'text': ':'.join(msg.split(':')[1:]).strip()} for msg in messages]}
            client_socket.sendall(json.dumps(response).encode('utf-8'))
        else:
            client_socket.sendall(b'{"error": "Invalid request data"}')
    except json.JSONDecodeError:
        client_socket.sendall(b'{"error": "Invalid JSON"}')
    finally:
        client_socket.close()


def main(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    inputs.append(server_socket)
    
    print(f"Chat server started on {host}:{port}. Waiting for connections...")
    
    while True:
        readable, _, _ = select.select(inputs, [], [])
        
        for s in readable:
            if s == server_socket:
                handle_new_connection(server_socket)
            else:
                handle_client_message(s)

if __name__ == "__main__":
    # Ensure host and port are provided as command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 server_modified.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    main(host, port)
