#!/usr/bin/python
# Create pointsets based on the config data specified, with random attribute values

import fiona
from sys import argv, stderr
from numpy.random import choice
from random import randint
from zipfile import ZipFile
from shapely.geometry import shape
from gzip import GzipFile
import yaml
import tempfile
import boto
import requests
import json

temp = tempfile.mkdtemp() + '/'

if len(argv) != 3:
    print >> stderr, 'usage: createPointsets.py config.yaml s3-pointset-bucket'
    exit(1)

with open(argv[1]) as configTxt:
    config = yaml.load(configTxt)

s3 = boto.connect_s3()
bucket = s3.get_bucket(argv[2])

for graphId, graph in config.iteritems():
    print >> stderr, 'processing pointsets for graph %s' % graphId

    points = []

    for county in graph['census']:
        print >> stderr, 'county %s' % county
        # download and process the shapefiles one at a time
        r = requests.get('http://www2.census.gov/geo/tiger/TIGER2010/TABBLOCK/2010/tl_2010_%s_tabblock10.zip' % county)

        fn = temp + str(county) + '.zip'
        with open(fn, 'wb') as zf:
            for chunk in r.iter_content(100 * 1024):
                print >> stderr, '.',
                zf.write(chunk)

        print >> stderr, 'done'

        # unzip it and read the polygons
        with open(fn) as zfraw:
            zf = ZipFile(zfraw)
            zf.extractall(temp)

        with fiona.open(temp + 'tl_2010_%s_tabblock10.shp' % county) as shp:
            b = graph['bounds']
            points.extend([shape(f['geometry']).centroid for f in shp.filter(bbox=(b['west'], b['south'], b['east'], b['north']))])

    print ' read %s Census blocks' % len(points)

    # build the geojson.
    properties = ['prop%s' % i for i in range(50)]
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
                    'coordinates': (pt.x, pt.y)
                },
                'id': 'feat%s' % i,
                'properties': {
                    'structured': {p: randint(1, 1000) for p in properties}
                }
            }
            for i, pt in zip(range(len(points)), points)
        ]
    }

    fn = '%s_full.json.gz' % graphId
    with GzipFile(temp + fn, 'w') as out:
        json.dump(pointset, out)
    key = boto.s3.key.Key(bucket)
    key.key = fn
    key.set_contents_from_filename(temp + fn)


    # save the original geojson features
    features = pointset['features']

    for p in [.05, .3, .6]:
        pointset['features'] = choice(features, size=int(len(features) * p), replace=False).tolist()
        fn = '%s_%.2f.json.gz' % (graphId, p)
        with GzipFile(temp + fn, 'w') as out:
            json.dump(pointset, out)

        key = boto.s3.key.Key(bucket)
        key.key = fn
        key.set_contents_from_filename(temp + fn)
    print 'done'
