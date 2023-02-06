//usr/bin/cc "$0" -I. -I ~/.local/include -L ~/.local/lib -lswe -lm -ldl -o /tmp/x.out && exec /tmp/x.out "$@"

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
    char version[20] = {'\0'};
    swe_set_ephe_path("/usr/share/libswe/ephe/");
    printf("version %s\n", swe_version(version));
}

int main(int argc, char* argv[])
{
    if (argc != 2) {
        puts("./a.out STAR    # where STAR = ',41Ari' or 'Rohini', etc.");
        return 0;
    }

    double gh_day;
    char star[40];
    double x_equ[6] = {0};
    double x_sid[6] = {0};

    init_swisseph();
    strncpy(star, argv[1], sizeof(star));

    /* 21 Mar 499, 7:30:31.57 UT */
    double tjd_ut = swe_julday(499, 3, 21, 7 + 30./60 + 31.57/3600, SE_JUL_CAL);
    // double tjd_ut = swe_julday(560, 3, 21, 12.0, SE_JUL_CAL);
    // double tjd_ut = swe_julday(2023, 3, 21, 12.0, SE_GREG_CAL);

    double epsln = obliquity(tjd_ut);
    printf("obliquity %.7lf\n", epsln);

    // default Fagan/Bradley ayanamsa
    (void) swe_fixstar_ut(star, tjd_ut, SEFLG_SIDEREAL, x_sid, serr);
    printf("star '%s' x_sidereal {%.7lf, %.7lf}\n", star, x_sid[0], x_sid[1]);

    (void) swe_fixstar_ut(star, tjd_ut, SEFLG_EQUATORIAL, x_equ, serr);
    printf("star '%s' x_equatorial {%.7lf, %.7lf}\n", star, x_equ[0], x_equ[1]);

    double pl = equatorial_to_ss_polar(x_equ[0], epsln);
    printf("star '%s' SS polar longitude %.7f\n", star, pl);

    // find SS polar coordinates when Magha is at 126°40' sidereal ecliptic.
    // hard-coded values below are from output of fix_star_ayanamsa.cc
    epsln = obliquity(1840810.860424); // zero ayanamsha jd for 126°40'
    double xx_sid[3] = {126.66666, 0.396248, 1.0}; // longitude, latitude, distance
    swe_cotrans(xx_sid, x_equ, -epsln); // ecliptic to equatorial coords
    pl = equatorial_to_ss_polar(x_equ[0], epsln); // equatorial to SS polar long
    printf("Regulus at SS polar longitude %.7f on its zero-day ayan\n", pl);

    // find SS polar coordinates when Antares (Jyestha) is at 226°40' sidereal ecliptic
    epsln = obliquity(1845266.271522); // zero ayanamsha jd for 126°40'
    double xy_sid[3] = {226.66666, -4.351188, 1.0}; // longitude, latitude, distance
    swe_cotrans(xy_sid, x_equ, -epsln); // ecliptic to equatorial coords
    pl = equatorial_to_ss_polar(x_equ[0], epsln); // equatorial to SS polar long
    printf("Jyestha at SS polar longitude %.7f on its zero-day ayan\n", pl);

    // Graha-laghava positions
    gh_day = swe_julday(1520, 3, 19, 6.0, SE_JUL_CAL);
    epsln = obliquity(gh_day);
    double expected = 48.5;
    xx_sid[0] = 47; xx_sid[1] = -5.6; xx_sid[2] = 1.0;
    swe_cotrans(xx_sid, x_equ, -epsln); // ecliptic to equatorial coords
    pl = equatorial_to_ss_polar(x_equ[0], epsln); // equatorial to SS polar long
    printf("Rohini (Aldebaran) sidereal [%.4f, %.4f] at SS polar longitude %.7f on its grha-laghava day. Expected %.1f\n",
           xx_sid[0], xx_sid[1], pl, expected);

    swe_close();
}

// In summary: Graha-laghava gives many matches to its table, if we assume TRUE_REVATI. Pancha-siddhantika gives better matches to TRUE_CITRA.
//
// Rohini-paksha ayanamsha seems best compromise. Satisfies all three -- SS, GL and PS.
// Rohini (Aldebaran) sidereal [46.6666, -5.6000] at SS polar longitude 48.2923257 on its graha-laghava day. Expected 49.00 (GL), 48.0 (Panchasiddhantika), 49.50 (Surya Siddhanta) --> zero ayan day at [+0340/07/10 21.4746]
// Rohini (Aldebaran) sidereal [47.0000, -5.6000] at SS polar longitude 48.6154108 on its grha-laghava day.  Expected 49.00 (GL), 48.0 (Panchasiddhantika), 49.50 (Surya Siddhanta) --> Zero ayan day at [+0364/07/11 23.2122]
// Punarvasu (Pollux) sidereal [93.3333, 6.5300] at SS polar longitude 93.507844 on its grha-laghava day. Expected 94.0 (GL), 88 (Panchasiddhantika), 93 (SS)
// Magha (Regulus) sidereal [126.6666, 0.3790] at SS polar longitude 126.7652541 on its graha-laghava day. Expected 129.00 (GL), 126.0 (Panchasiddhantika), 129 (SS)
// Citra (Spica) sidereal [180.0000, -1.9220] at SS polar longitude 179.1638906 on its graha-laghava day. Expected 183.00 (GL), 180°50' (Panchasiddhantika), 180 (SS)
// Jyestha (Antares) sidereal [226.6666, -4.3512] at SS polar longitude 225.3336877 on its graha-laghava day. Expected 230.00 (GL), 229 (SS)
// Mula (Sabik) sidereal [234.1200, 7.2000] at SS polar longitude 235.8856992 on its graha-laghava day. Expected 242.0 (GL), 241 (SS)
// Mula (Shaula) sidereal [241.0000, -13.5100] at SS polar longitude 237.8089711 on its grha-laghava day. Expected 242.0 (GL), 241 (SS)
// Anuradha (Dscubba) sidereal [220.0000, -1.7300] at SS polar longitude 219.4185972 on its grha-laghava day. Expected 224.0 (GL), 224 (SS)
// Ashlesha (epHya) sidereal [109.0000, -11.2400] at SS polar longitude 107.5099665 on its grha-laghava day. Expected 107.0 (GL), 107.666 (Panchasiddhantika), 109 (SS)
// Pushya (deCnc) sidereal [106.0000, -0.0030] at SS polar longitude 105.9996404 on its grha-laghava day. Expected 106.0 (GL), 97.333 (Panchasiddhantika), 106 (SS)
// Revati (zePsc) sidereal [359.6660, -0.2400] at SS polar longitude -0.2296270 on its grha-laghava day. Expected 0.0, 359°50' (SS)
