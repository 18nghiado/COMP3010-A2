CC = gcc
CFLAGS = -Wall

all: screenscraper

screenscraper: screenscraper.c
	$(CC) $(CFLAGS) -o screenscraper screenscraper.c

clean:
	rm -f screenscraper
