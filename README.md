# Run analysis with random data and points from the Census using OTPA Broker on US cities

First, edit config.yaml to specify the cities you would like to test. The format is fairly straightforward: specify
the names of the cities you want to test, where to find their GTFS feeds, and the FIPS codes of the relevant counties
or states. The points in the pointsets will be clipped to those bounds.

Next, create the graphs. Do this by running

    VEX_SERVER=http://your-vex-server/ python createGraphs.py config.yaml <your-s3-graph-bucket>

with the name of the S3 bucket used to store graphs for your instance of Analyst. The script will download GTFS and OSM
and will upload graph files. The `VEX_SERVER` environment variable specifies the URL of an [OSM-lib server](https://github.com/conveyal/osm-lib).

Next, create the pointsets. Do this by running

    python createPointsets.py config.yaml <your-s3-pointset-bucket>

Finally, start the jobs by running

    python runJobs.py config.yaml [broker-url]

If omitted, the broker URL defaults to `http://localhost:9001`
