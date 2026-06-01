CC      = mpicc
CFLAGS  = -O2 -Wall
LDFLAGS = -lm

all: sinwave sinwave_data

sinwave: sinwave.c pgm.c pgm.h
	gcc $(CFLAGS) -o $@ sinwave.c pgm.c $(LDFLAGS)

sinwave_data: sinwave_data.c pgm.c pgm.h
	$(CC) $(CFLAGS) -o $@ sinwave_data.c pgm.c $(LDFLAGS)

clean:
	rm -f sinwave sinwave_data *.pgm *.gif
