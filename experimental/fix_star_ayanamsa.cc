//usr/bin/c++ "$0" -Wall -Wextra -I. -I ~/.local/include -L ~/.local/lib -lswe -lm -ldl -o /tmp/a.out && exec /tmp/a.out "$@"

#include <ctime>
#include <swephexp.h>
#include "bisection.h"

// fix this star at that sidereal ecliptic longitude
static char fixed_star[32] = "Regulus"; // "Shaula"
static double fixed_long = 126+40/60.; // 241.0;

// All the following choices give Spica at 180±0.5°, so very close!
// Place Mula ("Shaula") at 241° -- both SS and Brahma-sphuta-siddhanta prescribe this value exactly
// Place Magha ("Regulus") at 126°40' -- middle of the nakshatra
// Place Rohini ("Aldebaran") at 46°40' -- middle of the nakshatra
// Place Pushya (",deCnc") at 105.5° -- still closer to prescribed 106°
// Place Jyestha ("Antares") at 226°40' -- exact beginning of the nakshatra, though SS and BSS give 229° polar long.
// Place Anuradha ("Dschubba") at 219° -- though 220° is exactly in middle of Anuradha
// Only oddball is Revati, which is close to 356° and not 359°50' as per SS
//
// As per all of the above, choose an ayanamsha whose zero date falls
// in range 300 - 350 CE. Every other ayanamsha is crap.

void init_swisseph(void)
{
    char version[20] = {'\0'};
    char path[] = "/usr/share/libswe/ephe/";

    swe_set_ephe_path(path);
    printf("sweph version %s\n", swe_version(version));
}

double fix_star_at_sidereal_longitude(double jd)
{
    double x[6] = {0};
    char err[256] = {'\0'};

    swe_set_sid_mode(SE_SIDM_USER, jd, 0);
    (void) swe_fixstar_ut(fixed_star, jd, SEFLG_SIDEREAL, x, err);

    if (err[0] != '\0') { puts(err); }

    double fval = norm180(x[0] - fixed_long);

    return fval;
}

int main(int argc, char *argv[])
{
    if (argc > 1 && argc != 3) {
        printf("%s STAR SIDEREAL_LONG #\ne.g.\t%s Aldebaran 46.6666\n", argv[0], argv[0]);
        return 0;
    }

    if (argc == 3) {
        strncpy(fixed_star, argv[1], sizeof(fixed_star));
        fixed_long = atof(argv[2]);
    }

    init_swisseph();

    double start = swe_julday(1, 1, 1, 12.0, SE_GREG_CAL);
    double stop = swe_julday(600, 1, 1, 12.0, SE_GREG_CAL);
    double root_jd = bisection(fix_star_at_sidereal_longitude, start, stop);
    double x[6];
    char err[256];
    int year, month, day;
    double time;

    swe_set_sid_mode(SE_SIDM_USER, root_jd, 0);
    (void) swe_fixstar_ut(fixed_star, root_jd, SEFLG_SIDEREAL, x, err);
    swe_revjul(root_jd, SE_GREG_CAL, &year, &month, &day, &time);

    printf("Fixed the star '%s' at sidereal long %.5f on jd %.6f = [%+05d/%02d/%02d %.4f]\n-----\n",
           fixed_star, fixed_long, root_jd, year, month, day, time);

    // print some common stars
    const int num_stars = 13;
    const char* stars[num_stars] = {
        "Regulus" /*Magha*/, "Shaula" /*Mula*/, "Antares" /*Jyestha*/, "Aldebaran" /*Rohini*/,
        "Alcyone" /*Krittika*/, ",SgrA*" /*Gal. center*/, "Spica" /*Citra*/, ",deCnc" /*Pushya*/,
        ",zePsc" /*Revati*/, "ZubenElgenubi" /*Visakha*/, "Dschubba" /*Anuradha*/,
        "Ashlesha" /*Ashlesha*/, "Pollux" /*Punarvasu*/ };

    for (int i = 0; i < num_stars; i++) {
        strcpy(fixed_star, stars[i]);
        (void) swe_fixstar_ut(fixed_star, root_jd, SEFLG_SIDEREAL, x, err);
        printf("%s sidereal ecliptic (%.6lf, %.6lf)° on jd %.6lf = [%+05d/%02d/%02d %.4f]\n",
           fixed_star, x[0], x[1], root_jd, year, month, day, time);
    }

    // Print the same table at modern times
    puts("---------");
    time_t t = std::time(NULL);
    struct tm ltime = {};
    localtime_r(&t, &ltime);

    year = ltime.tm_year + 1900; month = ltime.tm_mon + 1; day = ltime.tm_mday; time = 12.0;
    double jd = swe_julday(year, month, day, time, SE_GREG_CAL);

    for (int i = 0; i < num_stars; i++) {
        strcpy(fixed_star, stars[i]);
        (void) swe_fixstar_ut(fixed_star, jd, SEFLG_SIDEREAL, x, err);
        printf("%s sidereal ecliptic (%.6lf, %.6lf)° on jd %.6lf = [%+05d/%02d/%02d %.4f]\n",
           fixed_star, x[0], x[1], jd, year, month, day, time);
    }


    swe_close();
}
