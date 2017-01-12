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

from __future__ import print_function
import sys
import time

from novaclient import client as novaclient
from novaclient import exceptions as nova_exections

from utils import glance


def nova_client(session):
    return novaclient.Client('2.1', session=session)


def get_flavor(nova, name_or_id):
    try:
        flavor = nova.flavors.get(name_or_id)
        return flavor
    except nova_exections.NotFound:
        return nova.flavors.find(name=name_or_id)


def get_server(nova, name_or_id):
    try:
        server = nova.servers.get(name_or_id)
        return server
    except nova_exections.NotFound:
        return nova.servers.find(name=name_or_id)


def wait_instance(
    nova,
    instance,
    timeout=300,
    target_states=('active', 'shutoff'),
    transition_states=('build'),
    ):
    _timeout = 0
    status = instance.status.lower()
    while status not in target_states:
        if status not in transition_states:
            raise RuntimeError(
                'Fail to server "%s": %s (%s)' % (
                    target_states,
                    instance.name,
                    instance.status
                )
            )

        sys.stderr.write(
            'Waiting server %s: %s (%s)\n' % (
                target_states,
                instance.name,
                instance.status)
        )
        time.sleep(5)
        _timeout += 5
        if _timeout > timeout:
            raise RuntimeError("Timeout!")
        instance = nova.servers.get(instance.id)
        status = instance.status.lower()
