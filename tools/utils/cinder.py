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

from cinderclient import client as cinderclient
from cinderclient import exceptions as cinder_exections

from utils import nova


def cinder_client(session):
    return cinderclient.Client(2, session=session)


def get_volume(cinder, name_or_id):
    try:
        volume = cinder.volumes.get(name_or_id)
        return volume
    except cinder_exections.NotFound:
        return cinder.volumes.find(name=name_or_id)


def wait_instance(
    cinder,
    instance,
    timeout=300,
    target_states=('in-use', 'available'),
    transition_states=('creating'),
    status_attr='status',
    ):
    _timeout = 0
    status = getattr(instance, status_attr)
    while status not in target_states:
        if status not in transition_states:
            raise RuntimeError(
                'Fail to volume "%s": %s (%s)' % (
                    target_states,
                    instance.name,
                    instance.status
                )
            )

        sys.stderr.write(
            'Waiting volume %s: %s (%s)\n' % (
                target_states,
                instance.name,
                instance.status)
        )
        time.sleep(5)
        _timeout += 5
        if _timeout > timeout:
            raise RuntimeError("Timeout!")
        instance = cinder.volumes.get(instance.id)
        status = getattr(instance, status_attr)


def create_volume(env, name, volume, users, timeout=300):
    print("Start to create volume: {}".format(name), file=sys.stderr)

    session = users[volume['user']]['session']
    cinder = cinder_client(session)

    try:
        instance = get_volume(cinder, name)
        print(
            "[Warning]: Already exists volume: {}".format(name),
            file=sys.stderr,
        )
    except cinder_exections.NotFound:
        instance = cinder.volumes.create(
            volume['size'],
            name=name,
            volume_type=volume.get('type', None),
            availability_zone=env['env'].get('availability_zone', {})
                                        .get('cinder'),
        )

    # Set instancd id to env file
    volume['id'] = instance.id

    src = volume.get('src_hostname', None)
    if src:
        wait_instance(cinder, instance, timeout)
        if src != getattr(instance, 'os-vol-host-attr:host'):
            cinder.volumes.migrate_volume(
                instance,
                src,
                False,
                False,
            )
            instance = cinder.volumes.get(instance.id)
            wait_instance(
                cinder,
                instance,
                timeout,
                target_states=('success'),
                transition_states=(
                    'starting', 'migrating', 'completing'),
                status_attr='migration_status',
            )

    status = volume.get('status')
    attached_to = volume.get('attached_to')
    if status == 'in-use' and attached_to is not None:
        try:
            wait_instance(cinder, instance, timeout)
            nova_client = nova.nova_client(session)
            server_id = env['vm'][attached_to]['id']
            server = nova.get_server(nova_client, server_id)
            nova.wait_instance(nova_client, server, timeout)
            nova_client.volumes.create_server_volume(
                server_id,
                instance.id,
            )
        except KeyError:
            sys.stderr.write('No server attached to: %s \n' % attached_to)


def create_volumes(env, volumes, users):
    for name, volume in volumes.items():
        create_volume(env, name, volume, users, env.get('timeout', 300))


def delete_volume(env, name, volume, users, timeout=300):
    print("Start to delete volume: {}".format(name), file=sys.stderr)

    session = users[volume['user']]['session']
    cinder = cinder_client(session)
    try:
        volume = get_volume(cinder, name)
        volume.delete()
        wait_instance(
            cinder,
            volume,
            timeout=timeout,
            target_states=('deleted'),
            transition_states=('deleting', 'in-use', 'available'),
        )
    except cinder_exections.NotFound:
        print("Succeeded to delete volume:{}".format(name), file=sys.stderr)


def delete_volumes(env, volumes, users):
    for name, volume in volumes.items():
        delete_volume(env, name, volume, users, env.get('timeout', 300))
