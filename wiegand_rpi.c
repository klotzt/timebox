/*
 * Wiegand data reader with Raspberry Pi
 * Tested with RPi Model B rev2, and an 26bit Wiegand Cards
 * Spiros Ioannou 2017
 *
 * This is interrupt drivern, no polling occurs. 
 * After each bit is read, a timeout is set. 
 * If timeout is reached read code is evaluated for correctness.
 *
 * Wiegand Bits:
 * pFFFFFFFFNNNNNNNNNNNNNNNNP
 * p: even parity of F-bits and leftmost 4 N-bits
 * F: Facility code
 * N: Card Number
 * P: odd parity of rightmost 12 N-bits
 *
 * Compile with: gcc wiegand_rpi.c   -lwiringPi -lpthread -lrt  -Wall -o wiegand_rpi -O
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <memory.h>
#include <stdint.h>
#include <sys/time.h>
#include <signal.h>
#include <wiringPi.h>

/* Defaults, change with command-line options */
#define A0_PIN 0
#define A1_PIN 1
#define B0_PIN 2
#define B1_PIN 3

#define LED_PIN 24
#define BEEP_PIN 7

#define WIEGANDMAXBITS 40
#define READER_COUNT 2
/* Set some timeouts */

/* Wiegand defines:
 * a Pulse Width time between 20 μs and 100 μs (microseconds)
 * a Pulse Interval time between 200 μs and 20000 μsec
 */

/* Each bit takes 4-6 usec, so all 26 bit sequence would take < 200usec */
#define WIEGAND_BIT_INTERVAL_TIMEOUT_NSEC 200000*1000 /* interval between bits, typically 1000us */

struct wiegand_data{
    unsigned char p0, p1;       //parity 0 , parity 1
    uint8_t facility_code;
    uint16_t card_code;
    uint32_t full_code;;
    int code_valid;
    unsigned long bitcount;     // bits read
};
struct wiegand_data wds[READER_COUNT];

timer_t timerId[READER_COUNT];

struct option_s {
    int debug;
} options;

void show_code(int reader);
void wiegand_sequence_reset(int reader);
void reset_timeout_timer(long usec, int reader);
void gpio_init();

static struct timespec wbit_tm; //for debug

/* Timeout from last bit read, sequence may be completed or stopped */
void wiegand_timeout(int sig, siginfo_t *si, void *uc) {
	int reader=0;
	timer_t *tidp;
	tidp = si->si_value.sival_ptr;
	for (int i=0; i<READER_COUNT; i++)
	{
		if (&timerId[i]==tidp) reader=i;
	}
    if (options.debug)
        fprintf(stderr, "wiegand_timeout() for reader %d\n", reader);
    wiegand_sequence_reset(reader);
    show_code(reader);
}

void show_code(int reader) {
    if (wds[reader].code_valid) 
	{
			time_t timestamp; 
			char txt[100];
			time (&timestamp);
			strftime (txt, 100, "%H:%M:%S", localtime(&timestamp));
			printf ("0x%X,%s\n", wds[reader].full_code, txt);
			digitalWrite (LED_PIN, 1);
			digitalWrite (BEEP_PIN, 1);
			usleep(200000);
			digitalWrite (BEEP_PIN, 0);				
			digitalWrite (LED_PIN, 0);				
	}
    fflush(stdout);
}

int setup_wiegand_timeout_handler() {
	struct sigaction sa;
	sa.sa_flags = SA_SIGINFO;
	sa.sa_sigaction = wiegand_timeout;
	sigemptyset(&sa.sa_mask);
	if (sigaction(SIGRTMIN, &sa, NULL) == -1)
        perror("sigaction");
	for (int i=0; i<READER_COUNT; i++)
	{		
		struct sigevent sev;
		sev.sigev_notify = SIGEV_SIGNAL;
        sev.sigev_signo = SIGRTMIN;
        sev.sigev_value.sival_ptr = &timerId[i];
		if (timer_create(CLOCK_REALTIME, &sev, &timerId[i]) == -1)
		{
			printf ("Error creating timer %d\n", i);
		} 
			
	}
   
    return 0;
}

/* Parse Wiegand 26bit format 
 * Called wherever a new bit is read
 * bit: 0 or 1
 * reder: 0..READER_COUNT (number of card reader)
 */
void add_bit_w26(int bit, int reader) {
	static char parity0_calc[READER_COUNT];
	static char parity1_calc[READER_COUNT];
	
	// init with first bit
	if (wds[reader].bitcount == 0) {
        /* Reset */
        wds[reader].code_valid = 0;
        wds[reader].facility_code = 0;
        wds[reader].card_code = 0;
        wds[reader].full_code = 0;
        wds[reader].p0 = bit; // first parity
		wds[reader].p1 = 0;   
		parity0_calc[reader]=0;
		parity1_calc[reader]=0;
    } 
    //Parity calculation    
    if (wds[reader].bitcount > 0 && wds[reader].bitcount <= 12) {
        parity0_calc[reader] += bit;
    }
    else if (wds[reader].bitcount >= 13 && wds[reader].bitcount <= 24) {
        parity1_calc[reader] += bit;
    }
    //Code calculation
    if (wds[reader].bitcount > 0 && wds[reader].bitcount <= 8) {
        wds[reader].facility_code <<= 1;
        if (bit)
            wds[reader].facility_code |= 1;
    }
    else if (wds[reader].bitcount > 0 && wds[reader].bitcount < 25) {
        wds[reader].card_code <<= 1;
        if (bit)
            wds[reader].card_code |= 1;
    }
    else if (wds[reader].bitcount == 25) {
        wds[reader].p1 = bit;
        wds[reader].full_code = wds[reader].facility_code;
        wds[reader].full_code = wds[reader].full_code << 16;
        wds[reader].full_code += wds[reader].card_code;

        wds[reader].code_valid = 1;
        //check parity
        if ((parity0_calc[reader] % 2) != wds[reader].p0) {
            wds[reader].code_valid = 0;
            if (options.debug) {
                fprintf(stderr, "Incorrect even parity bit (leftmost): %d vs %d\n", parity0_calc[reader], wds[reader].p0);
            }
        }
        else if ((!(parity1_calc[reader] % 2)) != wds[reader].p1) {
            wds[reader].code_valid = 0;
            if (options.debug) {
                fprintf(stderr, "Incorrect odd parity bit (rightmost)\n");
            }
        }

    }
    else if (wds[reader].bitcount > 25) {
        wds[reader].code_valid = 0;
        wiegand_sequence_reset(reader);
    }

    if (wds[reader].bitcount < WIEGANDMAXBITS) {
        wds[reader].bitcount++;
    }

}

unsigned long get_bit_timediff_ns() {
    struct timespec now, delta;
    unsigned long tdiff;

    clock_gettime(CLOCK_MONOTONIC, &now);
    delta.tv_sec = now.tv_sec - wbit_tm.tv_sec;
    delta.tv_nsec = now.tv_nsec - wbit_tm.tv_nsec;

    tdiff = delta.tv_sec * 1000000000 + delta.tv_nsec;

    return tdiff;

}

void a0_pulse(void) {
    reset_timeout_timer(WIEGAND_BIT_INTERVAL_TIMEOUT_NSEC, 0);     //timeout waiting for next bit
    if (options.debug) {
        fprintf(stderr, "A Bit:%02ld, Pulse 0, %ld us since last bit\n",
                wds[0].bitcount, get_bit_timediff_ns() / 1000);
        clock_gettime(CLOCK_MONOTONIC, &wbit_tm);
    }
    add_bit_w26(0, 0);
}

void a1_pulse(void) {
    reset_timeout_timer(WIEGAND_BIT_INTERVAL_TIMEOUT_NSEC, 0);     //timeout waiting for next bit
    if (options.debug) {
        fprintf(stderr, "A Bit:%02ld, Pulse 1, %ld us since last bit\n",
                wds[0].bitcount, get_bit_timediff_ns() / 1000);
        clock_gettime(CLOCK_MONOTONIC, &wbit_tm);
    }
    add_bit_w26(1, 0);
}

void b0_pulse(void) {
    reset_timeout_timer(WIEGAND_BIT_INTERVAL_TIMEOUT_NSEC, 1);     //timeout waiting for next bit
    if (options.debug) {
        fprintf(stderr, "B Bit:%02ld, Pulse 0, %ld us since last bit\n",
                wds[1].bitcount, get_bit_timediff_ns() / 1000);
        clock_gettime(CLOCK_MONOTONIC, &wbit_tm);
    }
    add_bit_w26(0, 1);
}

void b1_pulse(void) {
    reset_timeout_timer(WIEGAND_BIT_INTERVAL_TIMEOUT_NSEC, 1);     //timeout waiting for next bit
    if (options.debug) {
        fprintf(stderr, "B Bit:%02ld, Pulse 1, %ld us since last bit\n",
                wds[1].bitcount, get_bit_timediff_ns() / 1000);
        clock_gettime(CLOCK_MONOTONIC, &wbit_tm);
    }
    add_bit_w26(1, 1);
}

void wiegand_sequence_reset(int reader) {
    wds[reader].bitcount = 0;
}

/* timeout handler, should fire after bit sequence has been read */
void reset_timeout_timer(long nsec, int reader) {
    struct itimerspec its;
	its.it_value.tv_sec = 0;
    its.it_value.tv_nsec = nsec;
    its.it_interval.tv_sec = 0;
    its.it_interval.tv_nsec = 0;
    
	if (timer_settime(timerId[reader], 0, &its, NULL) == -1)
	{
		perror("timer_settime");
	}
}

void gpio_init() {

    wiringPiSetup();
    pinMode(A0_PIN, INPUT);
    pinMode(A1_PIN, INPUT);
    pinMode(B0_PIN, INPUT);
    pinMode(B1_PIN, INPUT);
    pinMode (LED_PIN, OUTPUT);
	pinMode (BEEP_PIN, OUTPUT);
	
    wiringPiISR(A0_PIN, INT_EDGE_FALLING, a0_pulse);
    wiringPiISR(A1_PIN, INT_EDGE_FALLING, a1_pulse);
    wiringPiISR(B0_PIN, INT_EDGE_FALLING, b0_pulse);
    wiringPiISR(B1_PIN, INT_EDGE_FALLING, b1_pulse);


    digitalWrite (LED_PIN, 1);
	digitalWrite (BEEP_PIN, 1);
    sleep(1);
    digitalWrite (LED_PIN, 0);
	digitalWrite (BEEP_PIN, 0);
}
void show_usage() {
    printf("Wiegand Reader (https://bitbucket.org/sivann/wiegand_read)\n");
    printf("Usage: wiegand_read [-d] [-0 D0-pin] [-1 D1-pin]\n");
    printf("\t-d\t\tdebug\n");
    printf("\tCheck http://wiringpi.com/pins for WiringPi pin numbers\n");
    printf("\n");
}

int main(int argc, char *argv[]) 
{
    int opt;

    /* defaults */
    options.debug = 0;

    /* Parse Options */
    while ((opt = getopt(argc, argv, "d")) != -1) {
        switch (opt) {
        case 'd':
            options.debug++;
            break;
        case 'h':
            show_usage();
            exit(0);
            break;
        default:               /* '?' */
            show_usage();
            exit(EXIT_FAILURE);
        }
    }
	
    setup_wiegand_timeout_handler();
    gpio_init();
    wiegand_sequence_reset(0);
    wiegand_sequence_reset(1);

    while (1) {
        pause();
    }
}
