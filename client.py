import sys
import select
import termios
import socket

# Echo client program

try:
    name = sys.argv[1]
    server = sys.argv[2]
    port = int(sys.argv[3])
except:
    print("Usage: python filename.py myusername server port")
    sys.exit(1)

term_height = 23

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((server, port))
sock.setblocking(0)

# Canonical mode is "get input when enter is pressed"
# I want to read characters immediately!
fd = sys.stdin.fileno()
newattr = termios.tcgetattr(fd)
newattr[3] = newattr[3] & ~termios.ICANON
newattr[3] = newattr[3] & ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, newattr)

buildStr = ""
prev_chats = ["\n"] * term_height

while True:
    readable, writable, exceptional = select.select([sock, sys.stdin], [], [sock, sys.stdin])

    for r in readable:
        if r is sock:
            text = sock.recv(1024)
            if len(text) == 0:
                print("Goodbye")
                sys.exit(0)
            # read it, print it
            del prev_chats[0]
            prev_chats.append(text.decode('utf-8'))
            for c in prev_chats:
                print(c.strip())
            print(">> " + buildStr, end="", flush=True)
        else:
            # We have stdin, echo it, save it
            theChar = sys.stdin.read(1)
            print(theChar, end="", flush=True)
            buildStr = buildStr + theChar
            if theChar == "\n":
                buildStr = name + ": " + buildStr
                sock.send(buildStr.encode())
                buildStr = ""

    for e in exceptional:
        print(e)
