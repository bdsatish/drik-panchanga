//usr/bin/cc "$0" -I ~/.local/include -L ~/.local/lib -lswe -lm -ldl && exec ./a.out "$@"

#include <swephexp.h>
#include <math.h>

#define cosd(x) cos((x) * DEGTORAD)
#define tand(x) tan((x) * DEGTORAD)
#define atand(x) (atan(x) * RADTODEG)
#define atan2d(y, x) (atan2(y, x) * RADTODEG)

char serr[256];

double obliquity(double tjd_ut)
{
    double x[6];
    int ret = swe_calc_ut(tjd_ut, SE_ECL_NUT, 0, x, serr);
    return x[0];
}

double equatorial_to_ss_polar(double ra, double eps)
{
    double pl;  // result for polar longitude
    double coseps = cosd(eps);

    if (ra == 90 || ra == 270) {
        pl = ra;
    } else if (ra < 90 || ra > 270) {  // ra in quadrant 1 or 4
        pl = atand(tand(ra) / coseps);
    } else {  // ra > 90 and ra < 270, in quadrant 2 or 3
        double ra1 = 180 - ra;  // shift into quadrants 1 or 4
        double pl1 = atand(tand(ra1) / coseps);
        pl = 180 - pl1; // shift back into quadrants 2 or 3
    }

    return pl;
}

void init_swisseph(void)
{
    swe_set_ephe_path("/usr/share/libswe/ephe/");
    printf("version %s\n", swe_version(version));
}

int main(void)
{
    char star[40] = "Shaula";
    double x_equ[6] = {0};
    double x_sid[6] = {0};
    char version[100];

    init_swisseph();

    /* 21 Mar 499, 7:30:31.57 UT */
    // double tjd_ut = swe_julday(499, 3, 21, 7 + 30./60 + 31.57/3600, SE_JUL_CAL);
    // double tjd_ut = swe_julday(560, 3, 21, 12.0, SE_JUL_CAL);
    double tjd_ut = swe_julday(2023, 3, 21, 12.0, SE_JUL_CAL);

    double epsln = obliquity(tjd_ut);
    printf("obliquity %.7lf\n", epsln);

    // default Fagan/Bradley ayanamsa
    (void) swe_fixstar_ut(star, tjd_ut, SEFLG_SIDEREAL, x_sid, serr);
    printf("star '%s' x_sidereal {%.7lf, %.7lf}\n", star, x_sid[0], x_equ[1]);

    (void) swe_fixstar_ut(star, tjd_ut, SEFLG_EQUATORIAL, x_equ, serr);
    printf("star '%s' x_equatorial {%.7lf, %.7lf}\n", star, x_equ[0], x_equ[1]);

    double pl = equatorial_to_ss_polar(x_equ[0], epsln);
    printf("star '%s' SS polar longitude %.7f\n", star, pl);

    swe_close();
}
