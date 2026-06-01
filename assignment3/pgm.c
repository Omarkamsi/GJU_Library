#include <stdio.h>
#include <stdlib.h>
#include "pgm.h"

PGMImage* pgm_create(int width, int height, int maxval) {
    PGMImage *img = (PGMImage*)malloc(sizeof(PGMImage));
    if (!img) return NULL;

    img->width = width;
    img->height = height;
    img->maxval = maxval;

    img->data = (int*)malloc(width * height * sizeof(int));
    if (!img->data) {
        free(img);
        return NULL;
    }

    return img;
}

void pgm_free(PGMImage *img) {
    free(img->data);
    free(img);
}

void clear_image(PGMImage *img, int value) {
    int n = img->width * img->height;
    for (int i = 0; i < n; i++) {
        img->data[i] = value;
    }
}

void skip_comments(FILE *f) {
    int ch;

    while ((ch = fgetc(f)) != EOF) {
        if (ch == '#') {
            while ((ch = fgetc(f)) != '\n' && ch != EOF);
        } else if (ch != ' ' && ch != '\n' && ch != '\t' && ch != '\r') {
            ungetc(ch, f);
            return;
        }
    }
}

PGMImage* pgm_read(const char *filename) {
    FILE *f = fopen(filename, "r");
    if (!f) return NULL;

    char format[3];
    fscanf(f, "%2s", format);   // read P2

    //printf("%s\n", format);

    skip_comments(f);
    int width, height;
    fscanf(f, "%d %d", &width, &height);

    //printf("%d %d\n", width, height);

    skip_comments(f);
    int maxval;
    fscanf(f, "%d", &maxval);

    PGMImage *img = pgm_create(width, height, maxval);

    for (int i = 0; i < width * height; i++) {
        fscanf(f, "%d", &img->data[i]);
    }

    fclose(f);
    return img;
}

int pgm_write(const char *filename, const PGMImage *img) {
    FILE *f = fopen(filename, "w");

    fprintf(f, "P2\n");
    fprintf(f, "%d %d\n", img->width, img->height);
    fprintf(f, "%d\n", img->maxval);

    for (int i = 0; i < img->width * img->height; i++) {
        fprintf(f, "%d ", img->data[i]);
    }

    fclose(f);
    return 1;
}


/*
 * Goal:
 *   Convert a histogram (bins) into a grayscale image.
 *
 * Input:
 *   bins     : array of histogram counts
 *   nbins    : number of bins in the histogram
 *   width    : output image width (in pixels)
 *   height   : output image height (in pixels)
 *
 * Output:
 *   filename : PGM image file representing the histogram
 *
 * Description:
 *   - Each column in the image represents a bin
 *   - Bar height is proportional to bin value
 *   - Bars are drawn in black on a white background
 */

void pgm_write_histogram(
    const int *bins,
    int nbins,
    int width,
    int height,
    const char *filename
) {
    FILE *f = fopen(filename, "w");
    if (!f) {
        printf("Error: cannot open %s\n", filename);
        return;
    }

    int max_value = 0;
    for (int i = 0; i < nbins; i++) {
        if (bins[i] > max_value) {
            max_value = bins[i];
        }
    }

    if (max_value == 0) {
        printf("Warning: histogram is empty\n");
        fclose(f);
        return;
    }

    fprintf(f, "P2\n");
    fprintf(f, "%d %d\n", width, height);
    fprintf(f, "255\n");

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int bin = x * nbins / width;
            int bar_height = bins[bin] * height / max_value;

            if (y >= height - bar_height) {
                fprintf(f, "0 ");
            } else {
                fprintf(f, "255 ");
            }
        }
        fprintf(f, "\n");
    }

    fclose(f);
}