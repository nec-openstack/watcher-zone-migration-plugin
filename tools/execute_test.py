#!/usr/bin/python

import json
import subprocess
import sys

GOAL = "192afd7b-84b2-48a0-b755-b2b1b5a3227b"
STRATEGY = "85d39b54-6bd4-4cd4-8e92-920498388742"

def main(args):

    with open(args[1], 'r') as f:
        obj = json.load(f)

        subprocess.check_output(["watcher",
                         "audit",
                         "create",
                         "-g",
                         GOAL,
                         "-s",
                         STRATEGY,
                         "-p",
                         "params=" + json.dumps(obj)
                     ])

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Please give params file as first parameter")
        print("no command executed")
        sys.exit(1)
    elif len(sys.argv) >= 3:
        print("only single parameter acceptable")
        print("no command executed")
        sys.exit(1)

    main(sys.argv)
