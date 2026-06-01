CC = gcc
CFLAGS = -O2 -Wall -fopenmp

all: image_negative

pgm.o: pgm.c pgm.h
	$(CC) $(CFLAGS) -c pgm.c -o pgm.o

image_negative: image_negative.c pgm.o pgm.h
	$(CC) $(CFLAGS) image_negative.c pgm.o -o image_negative

clean:
	rm -f pgm.o image_negative negative_seq.pgm negative_par.pgm
