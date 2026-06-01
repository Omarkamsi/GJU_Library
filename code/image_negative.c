#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include "pgm.h"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input.pgm>\n", argv[0]);
        return 1;
    }

    /* Read input image */
    PGMImage input;
    if (pgm_read(argv[1], &input) != 0) {
        fprintf(stderr, "Error reading input image\n");
        return 1;
    }

    size_t npixels = (size_t)input.width * input.height;
    printf("Image: %d x %d, maxval = %d, pixels = %zu\n",
           input.width, input.height, input.maxval, npixels);

    /* Allocate output images */
    PGMImage out_seq, out_par;
    pgm_alloc(&out_seq, input.width, input.height, input.maxval);
    pgm_alloc(&out_par, input.width, input.height, input.maxval);

    /* --- Sequential negative --- */
    double t0 = omp_get_wtime();
    for (size_t i = 0; i < npixels; i++) {
        out_seq.data[i] = (unsigned char)(input.maxval - input.data[i]);
    }
    double t1 = omp_get_wtime();
    double Tseq = t1 - t0;

    /* --- Parallel negative (OpenMP) --- */
    double t2 = omp_get_wtime();
    #pragma omp parallel for schedule(static)
    for (size_t i = 0; i < npixels; i++) {
        out_par.data[i] = (unsigned char)(input.maxval - input.data[i]);
    }
    double t3 = omp_get_wtime();
    double Tpar = t3 - t2;

    /* Report times and speedup */
    printf("Tseq = %.6f s\n", Tseq);
    printf("Tpar = %.6f s  (threads = %d)\n", Tpar, omp_get_max_threads());
    printf("Speedup = %.2f\n", Tseq / Tpar);

    /* Save output images */
    pgm_write("negative_seq.pgm", &out_seq);
    pgm_write("negative_par.pgm", &out_par);
    printf("Saved: negative_seq.pgm, negative_par.pgm\n");

    /* Cleanup */
    pgm_free(&input);
    pgm_free(&out_seq);
    pgm_free(&out_par);

    return 0;
}
