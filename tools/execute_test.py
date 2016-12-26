#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

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
                                 "params=" + json.dumps(obj)])

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
