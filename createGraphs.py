#!/usr/bin/python
# Create graph bundles for the cities specified in the config file.
# usage: createGraphs.py config.yaml graph-bucket-name

from sys import argv
import yaml
import tempfile
import urllib
import uuid
import requests
import boto.s3
from zipfile import ZipFile
from os import environ

temp = tempfile.mkdtemp() + '/'

if len(argv) != 3   :
    print 'usage: createGraphs.py config.yaml graph-bucket-name'
    exit(1)

with open(argv[1]) as configFile:
    config = yaml.load(configFile)

s3 = boto.connect_s3()
bucket = s3.get_bucket(argv[2])

for graphId, graph in config.iteritems():
    print 'processing graph %s' % graphId

    # download all the GTFS files
    print '  retrieving GTFS'
    with ZipFile(temp + graphId + '.zip', 'w') as out:
        for feed, i in zip(config[graphId]['gtfs'], range(len(config[graphId]['gtfs']))):
            print '    %s' % feed

            fn = temp + uuid.uuid4().hex + '.zip'
            r = requests.get(feed, stream=True)

            with open(fn, 'wb') as gtfs:
                for chunk in r.iter_content(100 * 1024):
                    print '.',
                    gtfs.write(chunk)

            print ' done.'

            out.write(fn, str(i) + '.zip')

        print '  retrieving OSM'

        r = requests.get('%s/%s,%s,%s,%s.pbf' % (environ['VEX_SERVER'], graph['bounds']['south'], graph['bounds']['west'], graph['bounds']['north'], graph['bounds']['east']), stream=True)

        fn = temp + graphId + '.osm.pbf'

        with open(fn, 'wb') as osm:
            for chunk in r.iter_content(100 * 1024):
                print '.',
                osm.write(chunk)

        out.write(fn, graphId + '.osm.pbf')

    # Upload to S3
    # TODO: multipart uploads
    key = boto.s3.key.Key(bucket)
    key.key = graphId + '.zip'
    key.set_contents_from_filename(temp + graphId + '.zip')
    print done
