CC=gcc
CFLAGS=-I. -Wall -O
DEPS = wiegand_rpi.h
LIBS = -lwiringPi -lpthread -lrt 
OBJ = wiegand_rpi.o 

binaries=wiegand_rpi

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

wiegand_rpi: $(OBJ)
	gcc -o $@ $^ $(CFLAGS) $(LIBS)

all: $(binaries)

clean:
	rm -f *.o $(binaries)
