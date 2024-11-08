CC = gcc

all: screenscraper

screenscraper: screenscraper.c
	$(CC) -o screenscraper screenscraper.c

clean:
	rm -f screenscraper
