#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "pgm.h"

/* Skip comment lines (lines starting with '#') */
static void skip_comments(FILE *fp) {
    int c;
    while ((c = fgetc(fp)) == '#') {
        while ((c = fgetc(fp)) != '\n' && c != EOF)
            ;
    }
    ungetc(c, fp);
}

int pgm_alloc(PGMImage *img, int width, int height, int maxval) {
    img->width = width;
    img->height = height;
    img->maxval = maxval;
    img->data = (unsigned char *)malloc((size_t)width * height);
    if (!img->data)
        return -1;
    return 0;
}

void pgm_free(PGMImage *img) {
    if (img->data) {
        free(img->data);
        img->data = NULL;
    }
}

int pgm_read(const char *filename, PGMImage *img) {
    FILE *fp = fopen(filename, "rb");
    if (!fp) {
        fprintf(stderr, "pgm_read: cannot open '%s'\n", filename);
        return -1;
    }

    /* Read magic number */
    char magic[3];
    if (fscanf(fp, "%2s", magic) != 1) {
        fclose(fp);
        return -1;
    }

    if (strcmp(magic, "P5") != 0) {
        fprintf(stderr, "pgm_read: '%s' is not a binary PGM (P5) file\n", filename);
        fclose(fp);
        return -1;
    }

    skip_comments(fp);
    int width, height, maxval;
    if (fscanf(fp, "%d", &width) != 1) { fclose(fp); return -1; }
    skip_comments(fp);
    if (fscanf(fp, "%d", &height) != 1) { fclose(fp); return -1; }
    skip_comments(fp);
    if (fscanf(fp, "%d", &maxval) != 1) { fclose(fp); return -1; }

    if (maxval > 255) {
        fprintf(stderr, "pgm_read: maxval > 255 not supported\n");
        fclose(fp);
        return -1;
    }

    /* Consume single whitespace character after maxval */
    fgetc(fp);

    if (pgm_alloc(img, width, height, maxval) != 0) {
        fclose(fp);
        return -1;
    }

    size_t npixels = (size_t)width * height;
    if (fread(img->data, 1, npixels, fp) != npixels) {
        fprintf(stderr, "pgm_read: unexpected end of file\n");
        pgm_free(img);
        fclose(fp);
        return -1;
    }

    fclose(fp);
    return 0;
}

int pgm_write(const char *filename, const PGMImage *img) {
    FILE *fp = fopen(filename, "wb");
    if (!fp) {
        fprintf(stderr, "pgm_write: cannot open '%s'\n", filename);
        return -1;
    }

    fprintf(fp, "P5\n%d %d\n%d\n", img->width, img->height, img->maxval);

    size_t npixels = (size_t)img->width * img->height;
    if (fwrite(img->data, 1, npixels, fp) != npixels) {
        fprintf(stderr, "pgm_write: write error\n");
        fclose(fp);
        return -1;
    }

    fclose(fp);
    return 0;
}
