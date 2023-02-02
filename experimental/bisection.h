#pragma once

// A binary/bisection search for x, low <= x <= high, such that func(x) = 0
double bisection(double (*func)(double), double low, double high)
{
    const double epsilon = 1.0e-9;
    double mid;

    while ((high - low) > epsilon) {
        mid = (low + high) / 2;

        /* Optional: // if (func(mid) == 0.0) return mid; */

        if (func(mid) * func(low) < 0)
            high = mid;
        else
            low = mid;
    }

    return (low + high) / 2;
}

double norm180(double angle)
{
    return (angle >= 180) ? angle - 360 : angle;
}

double norm360(double angle)
{
    return fmod(angle, 360); // angle % 360
}
