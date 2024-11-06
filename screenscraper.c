#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netdb.h>

#define BUFFER_SIZE 4096

int create_socket(const char *host, int port) {
    struct hostent *server;
    struct sockaddr_in server_addr;

    server = gethostbyname(host);
    if (server == NULL) {
        fprintf(stderr, "ERROR: No such host\n");
        exit(1);
    }

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("ERROR opening socket");
        exit(1);
    }

    bzero((char *)&server_addr, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    bcopy((char *)server->h_addr, (char *)&server_addr.sin_addr.s_addr, server->h_length);
    server_addr.sin_port = htons(port);

    if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("ERROR connecting");
        exit(1);
    }

    return sock;
}

void send_request(int sock, const char *request) {
    if (write(sock, request, strlen(request)) < 0) {
        perror("ERROR writing to socket");
        exit(1);
    }
}

void receive_response(int sock, char *response) {
    bzero(response, BUFFER_SIZE);
    if (read(sock, response, BUFFER_SIZE - 1) < 0) {
        perror("ERROR reading from socket");
        exit(1);
    }
}

int main(int argc, char *argv[]) {
    if (argc < 5) {
        fprintf(stderr, "Usage: %s [host] [port] [username] [chat message]\n", argv[0]);
        exit(1);
    }

    const char *host = argv[1];
    int port = atoi(argv[2]);
    const char *username = argv[3];
    const char *message = argv[4];
    char response[BUFFER_SIZE];

    // Step 1: Check messages before posting (GET request)
    int sock = create_socket(host, port);
    char get_request[BUFFER_SIZE];
    snprintf(get_request, sizeof(get_request),
             "GET /api/messages HTTP/1.1\r\n"
             "Host: %s\r\n"
             "Cookie: username=%s\r\n\r\n", host, username);
    send_request(sock, get_request);
    receive_response(sock, response);
    close(sock);

    
    assert(strstr(response, "200 OK") != NULL); // Ensures the GET request is successful
    // Verify the message isn't present initially
    assert(strstr(response, message) == NULL);

    // Step 2: Send the message (POST request)
    sock = create_socket(host, port);
    char post_request[BUFFER_SIZE];
    snprintf(post_request, sizeof(post_request),
             "POST /api/messages HTTP/1.1\r\n"
             "Host: %s\r\n"
             "Content-Type: application/json\r\n"
             "Cookie: username=%s\r\n"
             "Content-Length: %lu\r\n\r\n"
             "{\"username\": \"%s\", \"text\": \"%s\"}",
             host, username, strlen(username) + strlen(message) + 20, username, message);
    send_request(sock, post_request);
    receive_response(sock, response);
    close(sock);

    assert(strstr(response, "200 OK") != NULL); // Ensures the POST request is successful

    // Step 3: Verify the message is now in the server's response (GET request)
    sock = create_socket(host, port);
    send_request(sock, get_request);
    receive_response(sock, response);
    close(sock);

    assert(strstr(response, "200 OK") != NULL); // Ensures the GET request is successful
    // Assert that the message now exists in the response
    assert(strstr(response, message) != NULL);

    // Step 4: Test unauthorized access without a cookie
    sock = create_socket(host, port);
    char unauth_request[BUFFER_SIZE];
    snprintf(unauth_request, sizeof(unauth_request),
             "GET /api/messages HTTP/1.1\r\n"
             "Host: %s\r\n\r\n", host);
    send_request(sock, unauth_request);
    receive_response(sock, response);
    close(sock);

    assert(strstr(response, "401 Unauthorized") != NULL); // Checks for proper unauthorized access response
    assert(strstr(response, "Unauthorized access") != NULL);

    printf("All tests passed!\n");

    return 0;
}
