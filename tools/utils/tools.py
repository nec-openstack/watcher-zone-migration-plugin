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

from cinderclient import exceptions as cinder_exections
from novaclient import exceptions as nova_exections

from utils import cinder
from utils import glance
from utils import keystone
from utils import neutron
from utils import nova


DEFAULT_PUB_KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC0ol7jQ4umQMr' \
                  'E1qtXnyeYk/23g6zVJyVPh0+rljElu/7zj6iJZtixxs+LebPH6m' \
                  'ZP13RIGPP0GlrSXRVBj9F2pjb/Y/PMyHBq3+BMeiYhn6XmNMwtT' \
                  'K2O69vvFZQi0M3wTVSezP9OxxrPay+eCXkGVi8lnh6ZDMrvSKI2' \
                  'c5SQ7wFJfT/4XTxzcP2gsotRV0rzADie1EF4MYke+ZJuiwnrFbZ' \
                  'peogrNtSvivR4f/g0/fD8NOjCKgbk4uY//6YhEqNaGhm0wABKt0' \
                  'MtimmxLLe2kosoFS539t88y5tD4ispcxlOAtVKZEL1ogf0VRrcB' \
                  'WSTfIiJty5vw6aRTfoFwuzZ hoge@example.com'


def find_or_create_users(keystone_client, users={}):
    _users = {}
    for key, user in users.items():
        _users[key] = user
        try:
            _users[key]['user'] = keystone.get_user(keystone_client, key)
        except ValueError:
            _users[key]['user'] = keystone.create_user(
                keystone_client, key, user)

        _users[key]['session'] = keystone.create_session(
            keystone_client.session.auth.auth_url,
            user,
        )

        pub_key = user.get('pub_key', DEFAULT_PUB_KEY)
        _users[key]['nova'] = nova.nova_client(_users[key]['session'])
        nova_client = _users[key]['nova']
        nova.delete_keypair(nova_client, key)
        nova.create_keypair(nova_client, key, pub_key)
    return _users


def delete_users(keystone_client, users={}):
    for user, _ in users.items():
        keystone.delete_user(keystone_client, user)


def create_server(env, name, vm, users, timeout=300):
    print("Start to create server: {}".format(name), file=sys.stderr)

    nova_client = users[vm['user']].get('nova', None)
    if nova_client is None:
        nova_client = nova.nova_client(users[vm['user']]['session'])
    glance_client = glance.glance_client(users[vm['user']]['session'])
    neutron_client = neutron.neutron_client(users[vm['user']]['session'])
    flavor = nova.get_flavor(nova_client, vm['flavor'])
    image = glance.get_image(glance_client, vm['image'])
    boot_volume = vm.get('boot_volume', None)
    nics = []
    network = vm.get('network', None)
    if network is not None:
        network = neutron.get_network(neutron_client, network)
        nics = [{'net-id': network['id']}]
    default_az = env['env'].get('availability_zone', {}).get('nova')
    availability_zone = vm.get(
        'availability_zone',
        default_az
    )

    az = None
    if vm.get('src_hostname', None):
        az = '{0}:{1}'.format(
            availability_zone,
            vm['src_hostname']
        )
    else:
        az = availability_zone

    userdata = vm.get('userdata', None)
    if userdata is not None:
        try:
            userdata = open(userdata)
        except IOError as e:
            print(
                "***[WARN]: Can't open: '{}'***".format(userdata),
                file=sys.stderr,
            )

    block_device_mapping_v2 = None
    if boot_volume:
        boot_volume['image_id'] = image.id
        boot_volume['user'] = vm['user']
        image = None
        volume = create_volume(
            env,
            "{}-volume".format(name),
            boot_volume,
            users,
            timeout
        )
        block_device_mapping_v2 = [
            {
                'uuid': volume.id,
                'source_type': 'volume',
                'destination_type': 'volume',
                'boot_index': 0,
                'delete_on_termination': True,
            }
        ]

    try:
        instance = nova.get_server(nova_client, name)
        print(
            "***[WARN]: Already exists server: {}***".format(name),
            file=sys.stderr,
        )
    except nova_exections.NotFound:
        instance = nova_client.servers.create(
            name=name,
            image=image,
            flavor=flavor,
            userdata=userdata,
            key_name=vm['user'],
            nics=nics,
            availability_zone=az,
            block_device_mapping_v2=block_device_mapping_v2,
        )

    # Set instancd id to env file
    vm['id'] = instance.id

    if vm.get('status', None) == 'shutoff':
        if instance.status.lower() != 'shutoff':
            nova.wait_instance(nova_client, instance, timeout)
            instance.stop()

    return instance


def create_servers(env, vms, users):
    for name, vm in vms.items():
        create_server(env, name, vm, users, env.get('timeout', 300))


def delete_server(env, name, vm, users, timeout=300):
    print("Start to delete server: {}".format(name), file=sys.stderr)

    nova_client = nova.nova_client(users[vm['user']]['session'])
    try:
        instance = nova.get_server(nova_client, name)
        instance.delete()
        nova.wait_instance(
            nova_client,
            instance,
            timeout=timeout,
            target_states=('deleted'),
            transition_states=('deleting', 'shutoff', 'active'),
        )
        boot_volume = vm.get('boot_volume', None)
        if boot_volume:
            boot_volume['user'] = vm['user']
            volume = delete_volume(
                env,
                "{}-volume".format(name),
                boot_volume,
                users,
                timeout
            )
    except nova_exections.NotFound:
        print("Succeeded to delete server:{}".format(name), file=sys.stderr)


def delete_servers(env, vms, users):
    for name, vm in vms.items():
        delete_server(env, name, vm, users, env.get('timeout', 300))


def create_volume(env, name, volume, users, timeout=300):
    print("Start to create volume: {}".format(name), file=sys.stderr)

    session = users[volume['user']]['session']
    cinder_client = cinder.cinder_client(session)
    image_id = volume.get('image_id', None)
    attached_to = volume.get('attached_to', None)
    default_az = env['env'].get('availability_zone', {}).get('cinder')
    availability_zone = volume.get(
        'availability_zone',
        default_az
    )

    try:
        instance = cinder.get_volume(cinder_client, name)
        print(
            "***[WARN]: Already exists volume: {}***".format(name),
            file=sys.stderr,
        )
    except cinder_exections.NotFound:
        instance = cinder_client.volumes.create(
            volume.get('size', 10),
            name=name,
            imageRef=image_id,
            volume_type=volume.get('type', None),
            availability_zone=availability_zone,
        )

    # Set instancd id to env file
    volume['id'] = instance.id

    src = volume.get('src_hostname', None)
    if src:
        cinder.wait_instance(cinder_client, instance, timeout)
        if src != getattr(instance, 'os-vol-host-attr:host'):
            cinder_client.volumes.migrate_volume(
                instance,
                src,
                False,
                False,
            )
            instance = cinder_client.volumes.get(instance.id)
            cinder.wait_instance(
                cinder_client,
                instance,
                timeout,
                target_states=('success'),
                transition_states=(
                    'starting', 'migrating', 'completing'),
                status_attr='migration_status',
            )

    if attached_to is not None or image_id is not None:
        cinder.wait_instance(cinder_client, instance, timeout)

    if attached_to is not None:
        volume['status'] = 'in-use'
        try:
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
    else:
        volume['status'] = 'available'

    return instance


def create_volumes(env, volumes, users):
    for name, volume in volumes.items():
        create_volume(env, name, volume, users, env.get('timeout', 300))


def delete_volume(env, name, volume, users, timeout=300):
    print("Start to delete volume: {}".format(name), file=sys.stderr)

    session = users[volume['user']]['session']
    cinder_client = cinder.cinder_client(session)
    try:
        volume = cinder.get_volume(cinder_client, name)
        volume.delete()
        cinder.wait_instance(
            cinder_client,
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
