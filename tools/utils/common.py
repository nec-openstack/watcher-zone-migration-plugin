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
import os
import sys
import time
import yaml

from glanceclient import client as glanceclient
from glanceclient import exc as glance_exections
from keystoneauth1.exceptions import http as ks_exceptions
from keystoneauth1 import loading
from keystoneauth1 import session
from keystoneclient.v3 import client as keystoneclient
from novaclient import client as novaclient
from novaclient import exceptions as nova_exections


def load_target_env(path):
    with open(path, 'r') as io:
        return yaml.load(io)


def env(*args, **kwargs):
    """Returns the first environment variable set.

    If all are empty, defaults to '' or keyword arg `default`.
    """
    for arg in args:
        value = os.environ.get(arg)
        if value:
            return value
    return kwargs.get('default', '')


def admin_session(**kwargs):
    loader = loading.get_plugin_loader('v3password')
    auth = loader.load_from_options(**kwargs)
    return session.Session(auth=auth)


def keystone_client(session):
    keystone = keystoneclient.Client(session=session)
    return keystone


def nova_client(session):
    return novaclient.Client('2.1', session=session)


def glance_client(session):
    return glanceclient.Client('1', session=session)


def get_role(keystone, name_or_id):
    try:
        role = keystone.roles.get(name_or_id)
        return role
    except ks_exceptions.NotFound:
        roles = keystone.roles.list(name=name_or_id)
        if len(roles) == 0:
            raise ValueError('Role not Found: %s' % name_or_id)
        if len(roles) > 1:
            raise ValueError('Role name seems ambiguous: %s' % name_or_id)
        return roles[0]


def get_user(keystone, name_or_id):
    try:
        user = keystone.users.get(name_or_id)
        return user
    except ks_exceptions.NotFound:
        users = keystone.users.list(name=name_or_id)
        if len(users) == 0:
            raise ValueError('User not Found: %s' % name_or_id)
        if len(users) > 1:
            raise ValueError('User name seems ambiguous: %s' % name_or_id)
        return users[0]


def get_project(keystone, name_or_id):
    try:
        project = keystone.projects.get(name_or_id)
        return project
    except ks_exceptions.NotFound:
        projects = keystone.projects.list(name=name_or_id)
        if len(projects) == 0:
            raise ValueError('Project not Found: %s' % name_or_id)
        if len(projects) > 1:
            raise ValueError('Project name seems ambiguous: %s' % name_or_id)
        return projects[0]


def get_domain(keystone, name_or_id):
    try:
        domain = keystone.domains.get(name_or_id)
        return domain
    except ks_exceptions.NotFound:
        domains = keystone.domains.list(name=name_or_id)
        if len(domains) == 0:
            raise ValueError('Domain not Found: %s' % name_or_id)
        if len(domains) > 1:
            raise ValueError('Domain name seems ambiguous: %s' % name_or_id)
        return domains[0]


def get_flavor(nova, name_or_id):
    try:
        flavor = nova.flavors.get(name_or_id)
        return flavor
    except nova_exections.NotFound:
        return nova.flavors.find(name=name_or_id)


def get_image(glance, name_or_id):
    try:
        image = glance.images.get(name_or_id)
        return image
    except glance_exections.HTTPNotFound:
        images = glance.images.list()
        _images = []
        for image in images:
            if image.name == name_or_id:
                _images.append(image)
        if len(_images) == 0:
            raise ValueError('Image not Found: %s' % name_or_id)
        if len(_images) > 1:
            raise ValueError('Image name seems ambiguous: %s' % name_or_id)
        return _images[0]


def create_session(user):
    loader = loading.get_plugin_loader('v3password')
    auth = loader.load_from_options(
        auth_url=env('OS_AUTH_URL', default=None),
        password=user['password'],
        user_id=user['user'].id,
        project_id=user['user'].default_project_id)
    return session.Session(auth=auth)


def create_user(keystone, user):
    project = get_project(keystone, user['project'])
    domain = get_domain(keystone, user['domain'])
    _user = keystone.users.create(
        user['username'],
        password=user['password'],
        domain=domain,
        project=project,
    )
    for role in user['roles']:
        role = get_role(keystone, role)
        keystone.roles.grant(role.id, user=_user.id, project=project.id)
    return _user


def delete_user(keystone, user):
    try:
        user = get_user(keystone, user['username'])
        keystone.users.delete(user)
    except ValueError:
        pass


def create_users(keystone, users={}):
    _users = {}
    for key, user in users.items():
        _users[key] = user
        _users[key]['user'] = create_user(keystone, user)
        _users[key]['session'] = create_session(user)
    return _users


def delete_users(keystone, users={}):
    for _, user in users.items():
        delete_user(keystone, user)


def wait_instance(nova, instance, timeout=300):
    _timeout = 0
    while instance.status != 'ACTIVE':
        sys.stderr.write('Waiting server ACTIVE: %s\n' % instance.name)
        time.sleep(5)
        _timeout += 5
        if _timeout > timeout:
            raise RuntimeError("Timeout!")
        instance = nova.servers.get(instance.id)


def create_server(env, name, vm, users, timeout=300):
    nova = nova_client(users[vm['user']]['session'])
    glance = glance_client(users[vm['user']]['session'])
    flavor = get_flavor(nova, vm['flavor'])
    image = get_image(glance, vm['image'])

    az = None
    if vm['src_hostname']:
        az = '%s:%s' % (env['availability_zone'], vm['src_hostname'])

    instance = nova.servers.create(
        name=name,
        image=image,
        flavor=flavor,
        availability_zone=az,
    )

    if vm['status'] == 'shutoff':
        wait_instance(nova, instance, timeout)
        instance.stop()


def create_servers(env, vms, users):
    for name, vm in vms.items():
        create_server(env, name, vm, users, env.get('timeout', 300))
