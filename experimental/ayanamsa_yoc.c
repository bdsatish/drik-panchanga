//usr/bin/c++ "$0" -Wall -Wextra -I. -I ~/.local/include -L ~/.local/lib -lswe -lm -ldl -o /tmp/a.out && exec /tmp/a.out "$@"
// Ayanamsha Time of Coincidence calculator
//
// Finds the zero point of the sidereal ecliptic for a given type of ayanamsha
// All dates are (proleptic) Gregorian calendar
//
// Tested with SwissEph 2.10.03
// gcc $CPPFLAGS $LIBS -lm -lswe file.c

#include <swephexp.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

void init_swisseph(void)
{
    char version[32] = {'\0'};
    char path[256] = {'\0'};
    strcpy(path, getenv("HOME"));
    strcat(path, "/.local/share/swisseph/:/opt/packages/swisseph/ephe/:"
	         "/usr/local/share/swisseph/:/usr/share/libswe/ephe/:");
    //or setenv SE_EPHE_PATH
    swe_set_ephe_path(path);
    printf("sweph version %s\n", swe_version(version));
}

// normalize angle to lie in range [-180, 180) degrees
double wrap180(double angle)
{
    assert(angle >= 0 && angle <= 360);
    return angle > 180 ? angle - 360 : angle;
}

void to_dms(double deg)
{
    deg = wrap180(deg);
    int d = deg;
    double mins = ((deg - d) * 60);
    int m = mins;
    double s = (mins - m) * 60;
    printf("%03d:%02d:%011.8lf\n", d, m, s);
}

void galactic_center(void)
{
    double julday = swe_julday(550, 3, 9, 14 + 3/60. + 32.45/3600, SE_GREG_CAL);
    swe_set_sid_mode(SE_SIDM_USER, julday, 0.0);

    double position[10] = {0}; // longitude, latitude, distance, speed, etc
    char errmsg[512] = {0};
    char star[50];  strcpy(star, "Gal. Center");
    int errcode = swe_fixstar_ut(star,
                                 julday,
                                 SEFLG_SIDEREAL | SEFLG_SWIEPH,
                                 position,
                                 errmsg);
    to_dms(fmod(position[0], 30)); // prints 006:39:59.99998588 in 2.02
                                   // prints 006:40:0.00476062 in 1.80

    // As claimed in Swisseph for SS_REVATI
    julday = swe_julday(499, 3, 21, 7 + 30/60. + 21.57/3600, SE_GREG_CAL);
    swe_set_sid_mode(SE_SIDM_USER, julday, -0.79167046);
    strcpy(star, ",zePsc"); // Revati = Zeta Piscium (see fixstars.cat)
    errcode = swe_fixstar_ut(star,
                             julday,
                             SEFLG_SIDEREAL | SEFLG_SWIEPH,
                             position,
                             errmsg);
    printf("SS_REVATI_UT = %.8lf\n", position[0]);
    // Surya Siddhanta claims this is 359°50' but returns 359°43'18.4"

    // True_Revati of Swiss Eph puts it at 0° always
    swe_set_sid_mode(SE_SIDM_TRUE_REVATI, 0, 0);
    errcode = swe_fixstar_ut(star,
                             julday,
                             SEFLG_SIDEREAL | SEFLG_SWIEPH,
                             position,
                             errmsg);
    printf("True_Revati_UT = %.8lf\n", position[0]);   // prints 0.00000000

    // TRUE_REVATI As discovered by me
    julday = swe_julday(563, 7, 20, 19 + 16/60. + 2.17/3600, SE_GREG_CAL);
    swe_set_sid_mode(SE_SIDM_USER, julday, 0.0);
    errcode = swe_fixstar_ut(star,
                             julday,
                             SEFLG_SIDEREAL | SEFLG_SWIEPH,
                             position,
                             errmsg);
    printf("Revati_UT @ 390°50' = %.8lf\n", position[0]);
    // prints 359.83333333 == 359°50'00' exactly
}

typedef double (*func1_t)(double);

double get_star_position(const char* star_, double point)
{
    double position[10] = {0}; // longitude, latitude, distance, speed, etc
    char errmsg[512] = {0};
    char star[50];
    int errcode;

    swe_set_sid_mode(SE_SIDM_USER, point, 0.0);

    strcpy(star, star_);

    // (not fixstar_ut)
    errcode = swe_fixstar(star,
                          point,
                          SEFLG_SIDEREAL | SEFLG_SWIEPH,
                          position,
                          errmsg);

    if (errcode == 0) { printf("%s: %s\n", __func__, errmsg); }
    return position[0];
}

double revati(double point)
{
    double fval = 0.0;

    // Place Revati at at 359°50'
    fval = wrap180(get_star_position("Revati", point)) - ((359 + 50/60.) - 360);
    return fval;
}

double gal_cent(double point)
{
    double fval = 0.0;

    // Place Galactic Center at middle of Mula (246°40')
    fval = get_star_position("Gal. Center", point) - (246 + 40/60.);
    return fval;
}

double rohini(double point)
{
    double fval = 0.0;

    // Place Aldebaran at middle of Rohini always 46°40'
    // String "Rohini" does not work here
    fval = get_star_position("Aldebaran", point) - (46 + 40/60.);
    return fval;
}

double ayan_func(double x)
{
    return wrap180(swe_get_ayanamsa(x));
}

// Find 'x' in range [start, stop] such that func(x) == 0.00
double bisection_search(func1_t func, double start, double stop)
{
    double left = start;
    double right = (stop > 0) ? stop : 2500000;  // JD = 31 Aug 2132
    double epsilon = 5E-10;

    do {
        double middle = (left + right) / 2.;
        double midval = func(middle);
        double rtval = func(right);

        if (midval * rtval >= 0.0) {
            right = middle;
        } else {
            left = middle;
        }

    } while (right - left > epsilon);

    return (right + left) / 2;
}

void ss_citra(void)
{
    swe_set_sid_mode(SE_SIDM_SS_CITRA, 0, 0);

    double dhour = 7 + 30/60. + 31.57/3600;
    double tjd_ut = swe_julday(499, 3, 21, dhour, SE_JUL_CAL);
    double daya = swe_get_ayanamsa_ut(tjd_ut);
    double daya_tt = swe_get_ayanamsa(tjd_ut);

    printf("\njd(UT) = %.14lf, SS_CITRA ayanamsha = %.15lf, (using wrong function = %.15lf)\n",
           tjd_ut, daya, daya_tt);

}

void date_conversion(void)
{
    int year, month, day, hour, min;
    double sec, timezone = 5.5;

    /* Local time to UTC. Enter +5.5 */
    swe_utc_time_zone(1985, 6, 9, 9, 40, 0, timezone,
                      &year, &month, &day, &hour, &min, &sec);

    printf("%d-%d-%d %d:%d:%lf\n", year, month, day, hour, min, sec);

    /* UTC to JD(UT1) */
    double jd[2];
    swe_utc_to_jd(year, month, day, hour, min, sec, SE_GREG_CAL, jd, NULL);
    printf("JD(ET) = %lf, JD(UT1) = %lf\n", jd[0], jd[1]);

    double djd = swe_julday(1985, 6, 9, 9 + 40/60., SE_GREG_CAL) - timezone/24.;
    double dt = swe_deltat(djd);
    double dut = djd + dt;
    printf("Using Julday (wrrooong): %lf\n", dut);

    /* JD(UT1) to UTC */
    swe_jdut1_to_utc(jd[1], SE_GREG_CAL, &year, &month, &day, &hour, &min, &sec);
    printf("UTC: %d-%d-%d %d:%d:%lf\n", year, month, day, hour, min, sec);

    /* UTC to local time zone. India is +5.5 but for UTC -> local, enter -5.5 */
    int y, m, d, h, mi;
    double dsec;
    swe_utc_time_zone(year, month, day, hour, min, sec, -timezone,
                      &y, &m, &d, &h, &mi, &dsec);
    printf("Local: %d-%d-%d %d:%d:%lf\n", y, m, d, h, mi, dsec);
}

int main(int argc, char* argv[])
{
    init_swisseph();
    double start = swe_julday(-100, 1, 1, 0, SE_GREG_CAL);  // 1 Jan 100 BCE
    double end = swe_julday(2100, 1, 1, 0, SE_GREG_CAL);    // 1 Jan 2100 CE
    
    const int c_ayanamsa_list[] =
       { SE_SIDM_FAGAN_BRADLEY,
         SE_SIDM_LAHIRI,
         SE_SIDM_DELUCE,
         SE_SIDM_RAMAN,
         SE_SIDM_USHASHASHI,
         SE_SIDM_KRISHNAMURTI,
         SE_SIDM_DJWHAL_KHUL,
         SE_SIDM_YUKTESHWAR,
         SE_SIDM_JN_BHASIN,
         SE_SIDM_BABYL_KUGLER1,
         SE_SIDM_BABYL_KUGLER2,
         SE_SIDM_BABYL_KUGLER3,
         SE_SIDM_BABYL_HUBER,
         SE_SIDM_BABYL_ETPSC,
         SE_SIDM_ALDEBARAN_15TAU,
         SE_SIDM_HIPPARCHOS,
         SE_SIDM_SASSANIAN,
         SE_SIDM_GALCENT_0SAG,
         SE_SIDM_J2000,
         SE_SIDM_J1900,
         SE_SIDM_B1950,
         SE_SIDM_SURYASIDDHANTA,
         SE_SIDM_SURYASIDDHANTA_MSUN,
         SE_SIDM_ARYABHATA,
         SE_SIDM_ARYABHATA_MSUN,
         SE_SIDM_SS_REVATI,
         SE_SIDM_SS_CITRA,
         SE_SIDM_TRUE_CITRA,
         SE_SIDM_TRUE_REVATI,
         SE_SIDM_TRUE_PUSHYA,
	 SE_SIDM_GALCENT_RGILBRAND,
	 SE_SIDM_GALEQU_IAU1958,
	 SE_SIDM_GALEQU_TRUE,
	 SE_SIDM_GALEQU_MULA,
	 SE_SIDM_GALALIGN_MARDYKS,
	 SE_SIDM_TRUE_MULA,
	 SE_SIDM_GALCENT_MULA_WILHELM,
	 SE_SIDM_ARYABHATA_522,
	 SE_SIDM_BABYL_BRITTON,
	 SE_SIDM_TRUE_SHEORAN,
	 SE_SIDM_GALCENT_COCHRANE,
	 SE_SIDM_GALEQU_FIORENZA,
	 SE_SIDM_VALENS_MOON,
	 SE_SIDM_LAHIRI_1940,
	 SE_SIDM_LAHIRI_VP285,
	 SE_SIDM_KRISHNAMURTI_VP291,
	 SE_SIDM_LAHIRI_ICRC
       };

    int num = (argc > 1) ? atoi(argv[1]) : 47;
    if (num > SE_NSIDM_PREDEF)   {  printf("%d: Out of range!\n", num); exit(1); }

    int ayanamsa_list[num];
    for (int i = 0; i < num; i++) { ayanamsa_list[i] = c_ayanamsa_list[i]; }

    double zero_points[num];
    int year, month, day;
    double hours;

    for (int i = 0; i < num; i++) {
        int ayan = ayanamsa_list[i];
        printf("%02d, ", ayan);
        printf("name = %-30s, ", swe_get_ayanamsa_name(ayan));

        swe_set_sid_mode(ayan, 0, 0);
        zero_points[i] = bisection_search(ayan_func, start, end);

        printf("julday = %0.8lf, ", zero_points[i]);

        swe_revjul(zero_points[i], SE_GREG_CAL, &year, &month, &day, &hours);
        printf("year = %+05d, month = %02d, day = %02d, hour = ", year, month, day);
        to_dms(hours);
    }

    for (int i = 0; i < num; i++) {
        int sid = ayanamsa_list[i];
        printf("%02d. ", sid);
        printf("name = %-30s, ", swe_get_ayanamsa_name(sid));
        swe_set_sid_mode(sid, 0, 0);

        double jd = 1927135.8747793;
        double ayan = swe_get_ayanamsa_ut(jd);
        to_dms(ayan);
    }
    galactic_center();

    ss_citra();

    // Fixed point of Revati@359°50
    double revati_359_50 = bisection_search(revati, start, end);
    printf("JD = %.9lf, Revati position: %.9lf\n",
           revati_359_50,
           get_star_position("Revati", revati_359_50));

    // Fixed point of Gal cent at mid-mula
    double gal_cent_mula = bisection_search(gal_cent, start, end);
    printf("JD = %.9lf = %d/%02d/%02d, Gal center position: %.9lf\n",
           gal_cent_mula, year, month, day,
           get_star_position("Gal. Center", gal_cent_mula));

    // Fixed point of Aldebaran at mid-Rohini
    double aldebaran = bisection_search(rohini, start, end);
    swe_revjul(aldebaran, SE_GREG_CAL, &year, &month, &day, &hours);
    printf("JD = %.9lf = %d/%02d/%02d, Aldebaran in Rohini: %.9lf\n",
           aldebaran, year, month, day,
           get_star_position("Aldebaran", aldebaran));
    
    date_conversion();
}
