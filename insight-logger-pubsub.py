#!/usr/bin/env python

import argparse
import sys
import json
import time
import os

from google.cloud import pubsub

from ouimeaux.environment import Environment
from ouimeaux.utils import matcher
from ouimeaux.signals import receiver, statechange, devicefound


def create_topic_if_needed(pubsub_client, topic_name):
  # Prepares the new topic
  topic = pubsub_client.topic(topic_name, timestamp_messages=True)
  if not topic.exists():
    topic.create()
    print('Topic {} created.'.format(topic.name))
  return topic


def publish_insight_data(topic, name, insight_params):
    data = insight_params
    data['lastchange'] = int(data['lastchange'].strftime("%s"))

    timestamp = int(time.strftime("%s"))
    json_data = "%s\n" % json.dumps({ "name": name, "timestamp": timestamp, "data":  data })
    topic.publish(json_data.encode('utf-8'))


def do(env, names, pubsub_client):
    for name in names:
        switch = env.get_switch(name)
        topic = create_topic_if_needed(pubsub_client, "insight_{}".format(name))
        publish_insight_data(topic, name, switch.insight_params)


def mainloop(names, pubsub_client, times=0, delay=10):
    env = Environment(with_cache=False)
    env.start()
    env.discover(5)

    if times < 1:
        while True:
            do(env,names,pubsub_client)
            time.sleep(delay)
    else:
        for i in range(0, times):
            do(env,names,pubsub_client)
            time.sleep(delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("insight-logger")
    parser.add_argument("--delay", type=int, default=10,
                        help="delay between device queries.")
    parser.add_argument("--times", type=int, default=0,
                        help="number of times to query the device.")
    parser.add_argument("name", metavar="SWITCHNAME", nargs="+",
                        help="Names of the WeMo Insight switch(es)")

    args = parser.parse_args()

    try:
        pubsub_client = pubsub.Client()
    except Exception as exception:
        print >>sys.stderr, "Error getting a pubsub client, exiting."
        print >>sys.stderr, exception
        sys.exit(1)

    try:
        mainloop(args.name, pubsub_client, times=args.times, delay=args.delay)
    except (KeyboardInterrupt,SystemExit) as ex:
        print >>sys.stderr, "Exiting"
        sys.exit(0)
