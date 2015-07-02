# create a CSV file of lat,lon from a BAG Compact database
# First unzip the top-level zip, then run this on the 9999GEO...zip found inside

from sys import argv
from csv import DictWriter
from numpy.random import uniform
from os.path import exists
from lxml import etree
from pyproj import Proj, transform
from zipfile import ZipFile
import json
import re

if len(argv) == 3:
    inf = argv[1]
    out = argv[2]
    n = None

elif len(argv) == 7:
    inf = argv[1]
    n1 = float(argv[2])
    e1 = float(argv[3])
    s1 = float(argv[4])
    w1 = float(argv[5])

    n = max(n1, s1)
    e = max(e1, w1)
    s = min(n1, s1)
    w = min(e1, w1)

    print n, e, s, w

    out = argv[6]


else:
    print 'usage: bagPointset.py input [n e s w] out.json'
    exit(1)


"Read a BAG geo zip and return a list of WGS 84 coordinates"
wgs84 = Proj(init='epsg:4326')
nl = Proj(init='epsg:28992')

with ZipFile(inf) as inf:
    with open(out, 'w') as outTxt:
        w = DictWriter(outTxt, ['lat', 'lon'])
        w.writeheader()

        count = 0

        for fn in inf.namelist():
            print fn
            xmlin = inf.open(fn)
            tree = etree.parse(xmlin)
            xmlin.close()

            # all we care about is the coordinates
            for pos in tree.findall('.//{http://www.opengis.net/gml}pos'):
                pos = [float(coord) for coord in pos.text.split(' ')]
                lon, lat = transform(nl, wgs84, *pos)

                # take a sample of 10% if we're not extracting a region
                if n is not None:
                    if lat > n or lat < s or lon > e or lon < w:
                        continue
                elif uniform(size=1)[0] > 0.1:
                    continue

                w.writerow(dict(lat=lat, lon=lon))
                count += 1

                if count % 1000 == 0:
                    print count

print 'read %s bag points' % count
