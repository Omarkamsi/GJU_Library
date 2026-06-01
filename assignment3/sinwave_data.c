/*
 * MPI Data-Parallel Sine Wave Animation
 *
 * Each process computes a vertical strip of columns for every frame.
 * Strips are gathered to rank 0 which writes PGM files.
 *
 * Usage: mpiexec -n <P> ./sinwave_data -l <lambda> [-v speed] [-f frames] [-t Tseq]
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <mpi.h>
#include "pgm.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static void help(const char *prog) {
    printf("Usage: %s -l <lambda> [-v speed] [-f frames] [-t Tseq]\n", prog);
    printf("  -l wavelength in pixels [required]\n");
    printf("  -v speed in pixels/frame (default 0)\n");
    printf("  -f number of frames (default 60)\n");
    printf("  -t sequential time Tseq for speedup calculation (default 0)\n");
    printf("Example:\n");
    printf("  mpiexec -n 4 %s -l 100 -v 5 -f 60 -t 0.250\n", prog);
}

static int parse(int argc, char **argv,
                 int *lambda, int *v, int *frames, double *tseq)
{
    *lambda = -1; *v = 0; *frames = 60; *tseq = 0.0;
    for (int i = 1; i < argc; i++) {
        if      (!strcmp(argv[i], "-l") && i+1 < argc) *lambda = atoi(argv[++i]);
        else if (!strcmp(argv[i], "-v") && i+1 < argc) *v      = atoi(argv[++i]);
        else if (!strcmp(argv[i], "-f") && i+1 < argc) *frames = atoi(argv[++i]);
        else if (!strcmp(argv[i], "-t") && i+1 < argc) *tseq   = atof(argv[++i]);
        else { help(argv[0]); return 0; }
    }
    return (*lambda > 0);
}

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int lambda, v, frames;
    double tseq;
    if (!parse(argc, argv, &lambda, &v, &frames, &tseq)) {
        if (rank == 0) help(argv[0]);
        MPI_Finalize();
        return 0;
    }

    const int w = 1400, h = 800, maxval = 255;
    const double k = 2.0 * M_PI / lambda;
    const int mid = h / 2;
    const int A   = h / 3;
    const int T   = (v == 0) ? 1 : frames;

    /* --- Data decomposition: divide columns among processes --- */
    int base_cols   = w / size;
    int x_start     = rank * base_cols;
    int x_end       = (rank == size - 1) ? w : x_start + base_cols;
    int local_cols  = x_end - x_start;

    /* Local strip: column-major within the strip [lx * h + y] */
    int *local_strip = malloc(local_cols * h * sizeof(int));
    if (!local_strip) { fprintf(stderr, "alloc fail\n"); MPI_Abort(MPI_COMM_WORLD, 1); }

    /* Rank 0 gather buffers */
    int *recv_buf   = NULL;
    int *sendcounts = NULL;
    int *displs     = NULL;

    if (rank == 0) {
        recv_buf   = malloc(w * h * sizeof(int));
        sendcounts = malloc(size * sizeof(int));
        displs     = malloc(size * sizeof(int));
        if (!recv_buf || !sendcounts || !displs) {
            fprintf(stderr, "alloc fail\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        int offset = 0;
        for (int r = 0; r < size; r++) {
            int xs = r * base_cols;
            int xe = (r == size - 1) ? w : xs + base_cols;
            int lc = xe - xs;
            sendcounts[r] = lc * h;
            displs[r]     = offset;
            offset       += lc * h;
        }
    }

    double tcomp = 0.0, tcomm = 0.0;

    for (int t = 0; t < T; t++) {

        /* Initialize strip to background */
        for (int i = 0; i < local_cols * h; i++) local_strip[i] = 20;

        /* --- Computation --- */
        double t0 = MPI_Wtime();

        for (int lx = 0; lx < local_cols; lx++) {
            int x       = x_start + lx;
            double yamp = A * sin(k * (x - v * t));
            int y       = (int)(mid - yamp);
            if (y >= 0 && y < h)
                local_strip[lx * h + y] = 255;
        }

        double t1 = MPI_Wtime();
        tcomp += t1 - t0;

        /* --- Communication: gather strips to rank 0 --- */
        double tc0 = MPI_Wtime();

        MPI_Gatherv(local_strip, local_cols * h, MPI_INT,
                    recv_buf, sendcounts, displs, MPI_INT,
                    0, MPI_COMM_WORLD);

        double tc1 = MPI_Wtime();
        tcomm += tc1 - tc0;

        /* --- Rank 0: assemble full image and write PGM --- */
        if (rank == 0) {
            PGMImage *img = pgm_create(w, h, maxval);

            int offset = 0;
            for (int r = 0; r < size; r++) {
                int xs = r * base_cols;
                int xe = (r == size - 1) ? w : xs + base_cols;
                int lc = xe - xs;
                for (int lx = 0; lx < lc; lx++) {
                    for (int y = 0; y < h; y++) {
                        img->data[y * w + (xs + lx)] = recv_buf[offset + lx * h + y];
                    }
                }
                offset += lc * h;
            }

            char filename[64];
            if (v == 0) snprintf(filename, sizeof(filename), "sin.pgm");
            else        snprintf(filename, sizeof(filename), "sin_%03d.pgm", t);

            pgm_write(filename, img);
            pgm_free(img);
        }
    }

    /* --- Reduce timing across all ranks (take max = slowest process) --- */
    double Tcomp_max, Tcomm_max;
    MPI_Reduce(&tcomp, &Tcomp_max, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&tcomm, &Tcomm_max, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        double Tpar     = Tcomp_max + Tcomm_max;
        double speedup  = (tseq > 0.0) ? tseq / Tpar : 0.0;

        printf("Tcomp   = %.6f s\n", Tcomp_max);
        printf("Tcomm   = %.6f s\n", Tcomm_max);
        printf("Tpar    = %.6f s\n", Tpar);
        if (tseq > 0.0)
            printf("Tseq    = %.6f s\n", tseq);
        printf("Speedup = %.4f\n", speedup);

        free(recv_buf);
        free(sendcounts);
        free(displs);
    }

    free(local_strip);
    MPI_Finalize();
    return 0;
}
