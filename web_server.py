import socket
import threading
import json
import os
import sys

HOST, PORT = '130.179.28.122', 8080

class WebServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Web server running on {self.host}:{self.port}...")
        
        while True:
            client_socket, _ = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        try:
            request = client_socket.recv(1024).decode()
            headers = request.split("\r\n")
            
            if headers and headers[0]:  # Check if headers is not empty and has a valid request line
                request_line = headers[0]
                parts = request_line.split()
                
                if len(parts) == 3:  # Ensure the request line has exactly 3 parts (method, path, HTTP version)
                    method, path, _ = parts

                    username = self.check_credentials(headers)  
                    
                    if not username and path not in ["/api/login", "/"]:
                        self.send_401(client_socket)
                        return
                    
                    if not path.startswith("/api") and path != "/":
                        self.serve_static_file(client_socket, path)
                    elif path == "/":
                        self.serve_static_file(client_socket, "/frontend.html")
                    else:
                        if method == "GET" and path == "/":
                            self.serve_html(client_socket)
                        elif method == "GET" and path.startswith("/api/messages"):
                            self.get_messages(client_socket, path)
                        elif method == "POST" and path == "/api/messages":
                            self.create_message(client_socket, headers, request)
                        elif method == "POST" and path == "/api/login":
                            request_body = request.split("\r\n\r\n")[1] if "\r\n\r\n" in request else ""
                            self.login(client_socket, headers, request_body)
                        elif method == "DELETE" and path == "/api/login":
                            self.logout(client_socket)
                        else:
                            self.send_404(client_socket)
                else:
                    self.send_400(client_socket)  # Handle malformed requests with a 400 Bad Request response
            else:
                self.send_400(client_socket)  # Handle cases where headers are empty or malformed
        except Exception as e:
            print("Error handling client:", e)
        finally:
            client_socket.close()

    def serve_static_file(self, client_socket, path):
        file_path = path.lstrip("/")
        
        if os.path.isfile(file_path):
            # Determine content type based on the file extension
            if file_path.endswith(".html"):
                content_type = "text/html"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                content_type = "image/jpeg"
            elif file_path.endswith(".png"):
                content_type = "image/png"
            elif file_path.endswith(".css"):
                content_type = "text/css"
            elif file_path.endswith(".js"):
                content_type = "application/javascript"
            else:
                content_type = "text/plain"  

            # Get the file size without reading the file content
            file_size = os.path.getsize(file_path)
            
            # Send the response headers
            response = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {file_size}\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            client_socket.sendall(response.encode('utf-8'))
            
            # Open the file in binary mode and stream it to the client
            with open(file_path, 'rb') as file:
                while chunk := file.read(4096):  
                    client_socket.sendall(chunk)
        else:
            # File not found, return 404
            response = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/html\r\n"
                "Connection: close\r\n"
                "\r\n"
                "<h1>404 Not Found</h1>"
            )
            client_socket.sendall(response.encode('utf-8'))
        
        client_socket.close()

    def serve_html(self, client_socket):
        if os.path.exists("frontend.html"):
            with open("frontend.html", "r") as file:
                content = file.read()
            server_url = f"http://{self.host}:{self.port}"
            content = content.replace("__SERVER_URL__", server_url)
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + content
        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\nFile not found."
        client_socket.sendall(response.encode())
        client_socket.close()

    def check_credentials(self, headers):
        # Check for username cookie in headers
        for header in headers:
            if header.startswith("Cookie:"):
                cookie_header = header.split("Cookie:")[1].strip()
                if "username=" in cookie_header:
                    return True
        return False


    def get_messages(self, client_socket, path):
        last_timestamp = 0
        if "last=" in path:
            try:
                last_timestamp = float(path.split("last=")[1])
            except ValueError:
                pass

        message_request = json.dumps({'get_messages': True, 'last': last_timestamp})
        response = self.forward_to_chat_server(message_request)

        if response:
            messages = json.loads(response).get("messages", [])
            self.send_json_response(client_socket, {'messages': messages})
        else:
            self.send_404(client_socket)

    def create_message(self, client_socket, headers, request):
        body = request.split("\r\n\r\n")[1]
        data = json.loads(body)
        message_request = json.dumps(data)
        response = self.forward_to_chat_server(message_request)

        if response:
            self.send_json_response(client_socket, json.loads(response))
        else:
            self.send_404(client_socket)

    def login(self, client_socket, headers, request_body):
        try:
            data = json.loads(request_body)
            username = data.get("username", "guest")  # Default to "guest" if no username is provided
        except json.JSONDecodeError:
            self.send_400(client_socket)
            return

        # Set the username cookie in the response
        response = f"HTTP/1.1 200 OK\r\nSet-Cookie: username={username}; Path=/; HttpOnly\r\n\r\n"
        client_socket.sendall(response.encode())
        client_socket.close()


    def logout(self, client_socket):
        response = "HTTP/1.1 200 OK\r\nSet-Cookie: username=; expires=Thu, 01 Jan 1970 00:00:00 UTC; Path=/; HttpOnly\r\n\r\n"
        client_socket.sendall(response.encode())
        client_socket.close()


    def forward_to_chat_server(self, data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as chat_socket:
                chat_socket.connect(('130.179.28.122', 9090))
                chat_socket.sendall(data.encode())
                response = chat_socket.recv(4096).decode()
                return response
        except Exception as e:
            print("Error forwarding to chat server:", e)
            return json.dumps({"error": "Could not connect to chat server"})

    def send_json_response(self, client_socket, data):
        response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" + json.dumps(data)
        client_socket.sendall(response.encode())
        client_socket.close()

    def send_404(self, client_socket):
        response = "HTTP/1.1 404 Not Found\r\n\r\n"
        client_socket.sendall(response.encode())
        client_socket.close()

    def send_401(self, client_socket):
        response = "HTTP/1.1 401 Unauthorized\r\n\r\nUnauthorized access."
        client_socket.sendall(response.encode())

    def send_400(self, client_socket):
        response = "HTTP/1.1 400 Bad Request\r\n\r\nMalformed request."
        client_socket.sendall(response.encode())


if __name__ == "__main__":
    # Ensure host and port are provided as command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 web_server.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    server = WebServer(host, port)
    server.start()
