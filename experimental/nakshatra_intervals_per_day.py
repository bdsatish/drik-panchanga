# Computes the average time interval (in days) between two successive nakshatras

from panchanga import *
from sys import exit
from numpy import diff, mean

# 1/1/2024  to 31/12/2025 gives 27.3248068, expected 27.321662
central_station = Place(23 + 11/60, 82.5, +5.5)
jd_start = gregorian_to_jd(Date(2033, 1, 1))
jd_end = gregorian_to_jd(Date(2037, 12, 31))

#print(jd_start, jd_end)

end_times = set() # to avoid kshaya nakshatras, we use set. Avoids duplicates
for i in range(int(jd_end - jd_start) + 1):
    nak = nakshatra(jd_start + i, central_station)
    hours = from_dms(*nak[1])
    ends = jd_start + i + hours / 24.
    end_times.add(ends) # first end time
    if len(nak) > 2:
        hours = from_dms(*nak[3])
        ends = jd_start + i + hours / 24.
        end_times.add(ends) # 2nd nakshatra on same day

#print(end_times)
#print(list(map(swe.revjul, end_times)))

differences = diff(list(end_times))

times = {}
for i in range(1, 28): times[i] = []
nak_index = 21 # nakshatra index on jd_start

for time in differences:
    times[nak_index].append(time)
    nak_index = 1 if nak_index == 27 else nak_index + 1

averages = {}
total = 0
for i in range(1, 28): averages[i] = 0
for key, value in times.items():
    averages[key] = mean(value)
    total += averages[key]

print(averages)
print(total)
