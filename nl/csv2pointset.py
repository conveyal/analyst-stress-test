# Sample (without replacement) from a CSV with lon and lat columns and create a pointset
# usage: csv2pointset.py infile.csv count outfile.json

from sys import argv
from random import randint
from numpy.random import choice
from csv import DictReader
import json

if len(argv) == 4:
    inf = argv[1]
    count = int(argv[2])
    outf = argv[3]
    n = None

else:
    print 'usage: csv2pointset.py in.csv [n e s w] count out.json'

pts = []

with open(inf) as inf:
    r = DictReader(inf)

    for row in r:
        pts.append((float(row['lon']), float(row['lat'])))

print 'read %s points' % len(pts)

# sample from them
pts = [pts[i] for i in choice(xrange(len(pts)), replace=False, size=count)]

properties = ['prop%s' % i for i in range(50)]

# write out the pointset
pointset = {
    'type': 'FeatureCollection',
    'properties': {
        'id': 'test',
        'schema': {p : {'style': {}, 'label': p} for p in properties},
    },
    'features': [
        {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': pt
            },
            'id': 'feat%s' % i,
            'properties': {
                'structured': {p: randint(1, 1000) for p in properties}
            }
        }
        for i, pt in zip(range(len(pts)), pts)
    ]
}

with open(outf, 'w') as outf:
    json.dump(pointset, outf)

            
    
