To run this code, it is recommended to run them in the same aviary machine, but if you don't want to, its fine also.

If you still decided to run these files on different aviary machines, follow this naming convention:
host_web: The host address of the terminal you use to run the web server web_server.py 
host_chat: The host address of the terminal you use to run the chat server server.py 
port_web and port_chat: You can choose any port you want for these, but they have to be different

First, we want to run the server.py using:
python3 server.py host_web port_chat
Example:
python3 server.py 130.179.28.112 8240

Next, we want to run the web_server.py using:
python3 web_server.py host_chat port_web port_chat
Example:
python3 web_server.py 130.179.28.116 8241 8240

After both of the servers are running, go on you browser, and type:
http://{host_web}:{port_web}/
Example:
http://130.179.28.112:8241/

Now you should be able to interact and test the chat on your browser

When you first opening up the chat on browser, you should see a login page, and in the "Network" tab, it should return error messages since you are not logged in right now. Enter an username into the bar to login.

If you want to test multiple web clients on browser, make sure to open up another browser since opening a new tab would just bring you to the logged in chat as describe in A2: "On return to the site, the user should stay logged in as that user."

To test the sharing images and files functionality, type this on the browser:
http://{host_web}:{port_web}/{path}
Example: 
http://130.179.28.112:8241/files/test.html

To test out the client.py file from assignment 1, type:
python3 client.py {username} {host_chat} {port_chat}
Example: 
python3 client.py john 130.179.28.116 8240

To test out the screenscraper.c in part 2, first compile it using:
make
Then run the file with:
./screenscraper {host_web} {port_web} {username} {chat message}
Example:
./screenscraper 130.179.28.112 8241 bob heyi
If you see "All tests passed!", that means the code worked and passed all the test in part 2!

