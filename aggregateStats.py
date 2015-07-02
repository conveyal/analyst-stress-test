# Simple SQS stats listener
# usage: aggregateStats.py <queue-name> <output.csv>

import boto.sqs
from csv import DictWriter
from sys import argv
import json
import traceback

conn = boto.sqs.connect_to_region('us-east-1')
q = conn.get_queue(argv[1])
q.set_message_class(boto.sqs.message.RawMessage)

received = 0

with open(argv[2], 'w') as outTxt:
    w = None

    computeSum = 0
    computeCount = 0

    try:
        while True:
            messages = q.get_messages(wait_time_seconds = 20, num_messages=10)
            for message in messages:
                received += 1

                if received % 100 == 0:
                    print 'received %s messages' % received
                    if computeCount > 0:
                        print 'avg compute time %sms' % (computeSum / computeCount)

                try:
                    body = json.loads(message.get_body())
                except:
                    print 'failed to parse message, will retry'
                    continue

                if w is None:
                    w = DictWriter(outTxt, sorted(body.keys()))
                    w.writeheader()

                w.writerow(body)

                if body['compute'] is not None:
                    computeSum += body['compute']
                    computeCount += 1

            if len(messages) > 0:
                q.delete_message_batch(messages)
    except:
        print traceback.format_exc()
        outTxt.close()
