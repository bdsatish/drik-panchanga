# Throw-away script for one-time use only.
#
# Generates cities.json of places whose population is more than 60000.
#
# Download cities15000.zip from http://download.geonames.org/export/dump/
#

import csv
import json
import os
import urllib.request
import zipfile

url = 'http://download.geonames.org/export/dump/cities15000.zip'
zip_path = '/tmp/cities15000.zip'
txt_path = '/tmp/cities15000.txt'
script_dir = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(txt_path):
    print('Downloading cities15000.zip ...')
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall('/tmp')
    os.remove(zip_path)
    print('Done.')

fin = open(txt_path, 'r')
reader = csv.reader(fin, 'excel-tab')
cities = {}

for record in reader:
    (geonameid, name, asciiname, alternatenames, latitude, longitude,
     featureclass, featurecode, countrycode, cc2, admin1code,
     admin2code, admin3code, admin4code, population,
     elevation, dem, timezone, modificationdate) = record

    # Ignore small cities
    if int(population) > 60000 and asciiname:
        cities[asciiname] = {
            'latitude': float(latitude),
            'longitude': float(longitude),
            'timezone': timezone,
        }

with open(os.path.join(script_dir, 'cities.json'), 'w') as fjson:
    json.dump(cities, fjson)

os.remove(txt_path)
