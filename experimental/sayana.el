(require 'calendar)
(require 'solar)

; Output from this code matches that of Python code (sayana-panchanga.py) exactly!

(defconst sayana-rasis
  '("Mesha" "Vrishabha" "Mithuna" "Karka"
    "Simha" "Kanya" "Tula" "Vrishchika"
    "Dhanus" "Makara" "Kumbha" "Meena"))

(defun get-solar-longitude (gregorian-date ut-hour)
    "Get true ecliptic longitude for a Gregorian DATE (month day year) and UT hour."
    (let* ((julian-centuries (solar-date-to-et gregorian-date ut-hour))
          ;; Passing UT centuries directly; the ~70s Delta-T difference
          ;; to Ephemeris Time is negligible for day boundaries.
          (coords (solar-ecliptic-coordinates julian-centuries t)))
      ; convert longitude to 0-360°
      (mod (car coords) 360)))

(defun calculate-sayana-date (year month day ut-hour)
  "Calculate the Sayana month and day for a Gregorian date and UT time."
  (let* ((gregorian-date (list month day year))
         (target-abs-date (calendar-absolute-from-gregorian gregorian-date))

         ;; 1. Get current longitude and determine the Rasi index
         (current-long (get-solar-longitude gregorian-date ut-hour))
         (target-rasi-idx (floor (/ current-long 30.0)))

         ;; 2. Search backward at 00:00 UT to find the Sankranti
         (sankranti-abs-date target-abs-date)
         (search-limit (- target-abs-date 32)))

    (while (and (> sankranti-abs-date search-limit)
                (= (floor (/ (get-solar-longitude
                              (calendar-gregorian-from-absolute sankranti-abs-date)
                              0.0)
                             30.0)) ; one rasi spans 30 deg
                   target-rasi-idx))
      (setq sankranti-abs-date (1- sankranti-abs-date)))

    ;; 3. Calculate the day
    ; First day of month is same as the Greg. date on which Sankranti occurs
    (let* ((day-one sankranti-abs-date)
           (sayana-day (1+ (- target-abs-date day-one)))
           (rasi-name (nth target-rasi-idx sayana-rasis)))

    (message "Gregorian Date: %04d-%02d-%02d %.03f UT | Sayana Date: %s %d | Longitude: %.2f°"
             year month day ut-hour
             rasi-name sayana-day
               current-long))))
