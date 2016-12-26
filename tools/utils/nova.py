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


def wait_instance(nova, instance, timeout=300, transition_states=('build')):
    _timeout = 0
    status = instance.status.lower()
    while status != 'active':
        if status not in transition_states:
            raise RuntimeError(
                'Fail to create server: %s (%s)' % (
                    instance.name,
                    instance.status
                )
            )

        sys.stderr.write(
            'Waiting server ACTIVE: %s (%s)\n' % (
                instance.name,
                instance.status)
        )
        time.sleep(5)
        _timeout += 5
        if _timeout > timeout:
            raise RuntimeError("Timeout!")
        instance = nova.servers.get(instance.id)
        status = instance.status.lower()


def create_server(env, name, vm, users, timeout=300):
    print("Start to create server: {}".format(name), file=sys.stderr)

    nova = nova_client(users[vm['user']]['session'])
    glance_client = glance.glance_client(users[vm['user']]['session'])
    flavor = get_flavor(nova, vm['flavor'])
    image = glance.get_image(glance_client, vm['image'])

    az = None
    if vm['src_hostname']:
        az = '%s:%s' % (env['env']['availability_zone'], vm['src_hostname'])

    instance = nova.servers.create(
        name=name,
        image=image,
        flavor=flavor,
        availability_zone=az,
    )
    # Set instancd id to env file
    vm['id'] = instance.id

    if vm['status'] == 'shutoff':
        wait_instance(nova, instance, timeout)
        instance.stop()


def create_servers(env, vms, users):
    for name, vm in vms.items():
        create_server(env, name, vm, users, env.get('timeout', 300))
