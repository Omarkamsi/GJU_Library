/*
SINE WAVE → IMAGE (COMPACT GUIDE)

Image:
(0,0) top-left, y increases downward
→ shift needed to center the wave

SPATIAL INPUT:
λ = wavelength (pixels per cycle)

Pixels → radians:
λ pixels = 2π radians
k = 2π / λ
angle = kx

Sine (math space):
sin(angle) ∈ [-1, +1]
y_math = A * sin(kx)   → [-A, +A], centered at 0

Map to image:
mid = height / 2
y = mid - y_math       (shift + flip)

Final:
y = mid - A * sin((2π/λ) * x)

TRAVELLING:
v = speed (pixels per frame)
t = frame index

x - vt = shifted position
angle = k(x - vt)

Final:
y = mid - A * sin((2π/λ) * (x - v*t))

Modes:
- 1D spatial      : v = 0
- 1D travelling   : v ≠ 0

Example (height=10, mid=5, A=3):

0
1
2  ← sin(π/2)   (top)
3
4
5  ← sin(0), sin(π), sin(2π) (center)
6
7
8  ← sin(3π/2) (bottom)
9
*/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>
#include "pgm.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static double w_clock() {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

// set pixel if inside image
static void set_pixel(PGMImage *img,int x,int y,int v){
    if(x>=0 && x<img->width && y>=0 && y<img->height)
        img->data[y*img->width + x] = v;
}

// filename: spatial→sin.pgm, travelling→sin_###.pgm
static void make_filename(char *n,size_t s,double v,int t){
    snprintf(n,s,(v==0.0)?"sin.pgm":"sin_%03d.pgm",t);
}

// help
static void help(const char *p){
    printf("Usage: %s -l <lambda> [-v speed] [-n frames]\n",p);
    printf("  -l wavelength in pixels [required]\n");
    printf("  -v speed in pixels/frame (default 0)\n");
    printf("  -n number of frames (default 60)\n");    
    printf("Example:\n");
    printf("  %s -l 100 -v 5 -n 60\n",p);
}

// parse args
static int parse(int argc, char **argv, int *lambda, int *v, int *frames){
    *lambda=-1; *v=0; *frames=60;

    for(int i=1;  i< argc; i++){
        if(!strcmp(argv[i],"-l")&&i+1<argc) *lambda=atoi(argv[++i]);
        else if(!strcmp(argv[i],"-v")&&i+1<argc) *v=atoi(argv[++i]);
        else if(!strcmp(argv[i],"-n")&&i+1<argc) *frames=atoi(argv[++i]);        
        else { help(argv[0]); return 0; }
    }

    return (*lambda>0);
}

int main(int argc,char **argv){
    // read input parameters
    int lambda, v, frames;
    if(!parse(argc,argv,&lambda,&v,&frames)){
        help(argv[0]);
        return 0;
    }

    // image size and wave constants
    const int w=1400, h=800, max=255;
    const double k=2.0*M_PI/lambda;
    const int mid=h/2;
    const int A=h/3;
    const int T=(v==0.0)?1:frames;

    // allocate all frames once
    PGMImage **frames_img = malloc(T * sizeof(PGMImage *));
    if(!frames_img){ fprintf(stderr,"alloc fail\n"); return 1; }

    for(int t=0;t<T;t++){
        frames_img[t] = pgm_create(w,h,max);
        if(!frames_img[t]){ fprintf(stderr,"alloc fail\n"); return 1; }
        clear_image(frames_img[t],20);
    }

    // Tseq measures computation only (no file writing)
    double start = w_clock();

    for(int t=0; t < T; t++){
        for(int x=0; x < w; x++){
            double y_amp = A * sin(k * (x - v*t));
            int y = (int)(mid - y_amp);
            set_pixel(frames_img[t], x, y, 255);
        }
    }

    double end = w_clock();
    double Tseq = end - start;

    // write frames after timing
    for(int t=0; t < T; t++){
        char filename[64];
        make_filename(filename,sizeof(filename),v,t);

        if(!pgm_write(filename, frames_img[t])){
            fprintf(stderr,"write fail\n");
            return 1;
        }

        pgm_free(frames_img[t]);
    }

    free(frames_img);

    printf("Tseq = %.6f s\n",Tseq);
    return 0;
}