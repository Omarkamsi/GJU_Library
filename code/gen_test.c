#include <stdio.h>
#include "pgm.h"

int main(void) {
    PGMImage img;
    int w = 4000, h = 4000;
    pgm_alloc(&img, w, h, 255);
    for (int i = 0; i < w * h; i++)
        img.data[i] = (unsigned char)(i % 256);
    pgm_write("test.pgm", &img);
    pgm_free(&img);
    printf("Generated test.pgm (%dx%d)\n", w, h);
    return 0;
}
