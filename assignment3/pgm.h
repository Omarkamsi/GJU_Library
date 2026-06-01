typedef struct {
    int width;
    int height;
    int maxval;
    int *data;
} PGMImage;

/* create, free, and clear image */
PGMImage* pgm_create(int width, int height, int maxval);
void pgm_free(PGMImage *img);
void clear_image(PGMImage *img, int value);

/* read and write */
PGMImage* pgm_read(const char *filename);
int pgm_write(const char *filename, const PGMImage *img);

/* histogram visualization */
void pgm_write_histogram(
    const int *bins,
    int nbins,
    int width,
    int height,
    const char *filename
);