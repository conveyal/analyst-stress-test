from csv import DictWriter
import boto
import json
from gzip import GzipFile
import uuid
import urllib2
import yaml
import requests
from random import randint
from time import time, sleep
from sys import argv

broker = argv[2] if len(argv) > 2 else 'http://localhost:9001'

with open(argv[1]) as configTxt:
    config = yaml.load(configTxt)

print 'connecting to broker %s' % broker

jobs = []

for graphId, graph in config.iteritems():
    # Many to many
    jobs.append(('%s_full' % graphId, '%s_full' % graphId, graphId))

    # vary the destination size
    jobs.extend([('%s_0.05' % graphId, '%s_%s' % (graphId, wh), graphId) for wh in ('0.05', '0.30', '0.60', 'full')])

print 'running %s jobs' % len(jobs)

# Download needed pointsets
s3 = boto.connect_s3()
b = s3.get_bucket('analyst-dev-pointsets')
for origin, destination, graphId in jobs:
    b.get_key(origin + '.json.gz').get_contents_to_filename(origin + '.json.gz')


def readPointset(psetId):
    gj = GzipFile(psetId + '.json.gz')
    ps = json.load(gj)
    gj.close()

    return [(f['geometry']['coordinates'][1], f['geometry']['coordinates'][0], i) for i, f in zip(range(len(ps['features'])), ps['features'])]

baseJobId = uuid.uuid4().hex[1:5]

w = DictWriter(open('jobs.csv', 'w'), ['job', 'timeSeconds'])

for origin, destination, graphId in jobs:
    print 'running job from %s to %s' % (origin, destination)

    origins = readPointset(origin)

    jobId = '%s_%s_%s' % (origin, destination, baseJobId)

    # set up the request
    req = [
        {
            'destinationPointsetId': destination,
            'graphId': graphId,
            'jobId': jobId,
            'id': 'feat%s' % i,
            'includeTimes': False,
            'outputLocation': 'analyst-frankfurt-results',
            'profileRequest' :  {
                "date":"2015-06-26",
                "fromTime": 7 * 3600,
                "toTime": 8 * 3600 +  (i % 60) * 60,
                "accessModes":"WALK",
                "egressModes":"WALK",
                "walkSpeed":1.3333333333333333,
                "bikeSpeed":4.1,
                "carSpeed":20,
                "streetTime":90,
                "maxWalkTime":20,
                "maxBikeTime":45,
                "maxCarTime":45,
                "minBikeTime":10,
                "minCarTime":10,
                "suboptimalMinutes":5,
                "analyst":True,
                "bikeSafe":1,
                "bikeSlope":1,
                "bikeTime":1,
                "scenario": None,
                "fromLat": lat,
                "fromLon": lon,
                "toLat": lat,
                "toLon": lon
            }
        } for lat, lon, i in origins
    ]

    # post it to the broker
    start = time()

    r = urllib2.Request(broker + '/enqueue/jobs')
    r.add_data(json.dumps(req))
    r.add_header('Content-Type', 'application/json')

    urllib2.urlopen(r).close()

    # wait for job to complete
    while True:
        sleep(10)

        r = requests.get(broker + '/status/' + jobId)
        if r.status_code == 404 or r.json()[0]['remaining'] == 0:
            w.writerow(dict(timeSeconds=time() - start, job=jobId))
            break
        else:
            print '%s complete, %s remain' % (r.json()[0]['complete'], r.json()[0]['remaining'])
