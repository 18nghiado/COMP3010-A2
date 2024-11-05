import socket
import select
import sys

def run_client():
    if len(sys.argv) != 4:
        print("Usage: python3 client.py <username> <host> <port>")
        return
    
    username = sys.argv[1] 
    HOST = sys.argv[2]
    PORT = int(sys.argv[3]) 
    server_address = (HOST, PORT)  
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(server_address)
        client_socket.sendall(username.encode('utf-8'))

        print(f"Connected to server as {username}.")
        
        while True:
            try:
                sockets_list = [sys.stdin, client_socket]
                
                readable, writable, exceptional = select.select(sockets_list, [], [])
                
                for sock in readable:
                    if sock == client_socket:
                        message = client_socket.recv(1024).decode('utf-8')
                        if message:
                            if "Connection refused" in message:
                                print(message)
                                client_socket.close()
                                return
                                
                            sys.stdout.write(f"\r{message}\n> ")  
                    else:
                        message = input("> ")
                        if message.lower() == "exit":
                            client_socket.sendall(f"{username} has left the chat.".encode('utf-8'))
                            client_socket.close()
                            print("Disconnected from server.")
                            return
                        else:
                            client_socket.sendall(f"{username}: {message}".encode('utf-8'))
            except KeyboardInterrupt:
                print("\nClient closed.")
                client_socket.close()
                return
    except ConnectionRefusedError as e:
        print(f"Unable to connect to server: {e}")
        return


if __name__ == "__main__":
    run_client()
