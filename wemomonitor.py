#!/usr/bin/env python

import argparse
import sys
import json
import time
import os

from ouimeaux.environment import Environment
from ouimeaux.utils import matcher
from ouimeaux.signals import receiver, statechange, devicefound

def write_to_file(name, insight_params, path):
    data = insight_params
    data['lastchange'] = int(data['lastchange'].strftime("%s"))

    dir = time.strftime("%Y/%m/%d/%H.%M.%S/data.json")
    fullpath = os.path.join(path, dir)
    try:
        os.makedirs(os.path.dirname(fullpath))
    except OSError as e:
        if e.errno == os.errno.EEXIST: pass
        else: raise

    with file(fullpath, "a") as f:
        timestamp = int(time.strftime("%s"))
        json_data = "%s\n" % json.dumps({ "name": name, "timestamp": timestamp, "data":  data })
        f.write(json_data)


def do(env, names, dir):
    for name in names:
        switch = env.get_switch(name)
        write_to_file(name, switch.insight_params, dir)


def mainloop(names, dir, times=0, delay=10):
    env = Environment(with_cache=False)
    env.start()
    env.discover(5)

    if times < 1:
        while True:
            do(env,names,dir)
            time.sleep(delay)
    else:
        for i in range(0, times):
            do(env,names,dir)
            time.sleep(delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Insight Poller")
    parser.add_argument("--delay", type=int, default=10,
                        help="delay between device queries.")
    parser.add_argument("--times", type=int, default=0,
                        help="number of times to query the device.")
    parser.add_argument("name", metavar="SWITCHNAME", nargs="+",
                        help="Names of the WeMo Insight switch(es)")

    parser.add_argument("--dir", help="Base directory to store data in", default="/tmp")
    args = parser.parse_args()
    try:
        mainloop(args.name, args.dir, times=args.times, delay=args.delay)
    except (KeyboardInterrupt,SystemExit) as ex:
        print >>sys.stderr, "Exiting"
        sys.exit(0)
