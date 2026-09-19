Wx GUI (Deprecated)
===================

**Deprecated:** The wxPython GUI (`gui.py`) is no longer actively maintained.
Use the [Web UI](../README.md#web-ui) or the PDF calendar scripts instead.
This page is kept for historical reference.

Running the GUI
---------------

```
apt-get install python3-tz python3-wxgtk4.0 python3-wheel
pip3 install --user pyswisseph  # or apt-get
python3 gui.py
```

Editing the GUI
---------------

Download [wxGlade](https://github.com/wxGlade/wxGlade/releases) and run:

```
python3 wxglade.py
```

then open `config/Gui.wxg`.

Using the GUI
-------------

### Location known

First, type the Date in DD/MM/YYYY format in the 'Date' field. Negative value for YYYY are
interpolated as proleptic Gregorian calendar.

Second, type your location (city or district) in the Location field and click 'Search'. If found,
then the coordinates and time zone are updated. If not, try the [next method](#location-unknown).
If your location's population is more than 50,000 then the location should be found.

Third, click 'Compute'. Now the fields like tithi, etc. are computed and shown on the GUI.

### Location unknown

First, type the Date in DD/MM/YYYY format in the 'Date' field.

Second, manually enter the coordinates and time zone of your location. You can use
[Google Maps](http://maps.google.com) or [Time and Date website](http://www.timeanddate.com/) for
this purpose.

Third, click 'Compute'. Now the fields like tithi, etc. are computed and shown on the GUI.
