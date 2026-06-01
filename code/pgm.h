#ifndef PGM_H
#define PGM_H

typedef struct {
    int width;
    int height;
    int maxval;
    unsigned char *data;
} PGMImage;

/* Read a PGM (P5 binary) image from file. Returns 0 on success, -1 on error. */
int pgm_read(const char *filename, PGMImage *img);

/* Write a PGM (P5 binary) image to file. Returns 0 on success, -1 on error. */
int pgm_write(const char *filename, const PGMImage *img);

/* Allocate image data. Returns 0 on success, -1 on error. */
int pgm_alloc(PGMImage *img, int width, int height, int maxval);

/* Free image data. */
void pgm_free(PGMImage *img);

#endif /* PGM_H */
