import os
import time
import sys
import yaml

from keystoneauth1 import loading
from keystoneauth1 import session
from keystoneauth1.exceptions import http as ks_exceptions
from keystoneclient.v3 import client as keystoneclient
from glanceclient import client as glanceclient
from glanceclient import exc as glance_exections
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

def keystone_admin_client():
    loader = loading.get_plugin_loader('v3password')
    auth = loader.load_from_options(
        auth_url = env('OS_AUTH_URL', default=None),
        password = env('OS_PASSWORD', default=None),
        username = env('OS_USERNAME', default=None),
        user_id = env('OS_USER_ID', default=None),
        user_domain_id = env('OS_USER_DOMAIN_ID', default=None),
        user_domain_name = env('OS_USER_DOMAIN_NAME', default=None),
        domain_id = env('OS_DOMAIN_ID', default=None),
        domain_name = env('OS_DOMAIN_NAME', default=None),
        project_id = env('OS_PROJECT_ID', default=None),
        project_name = env('OS_PROJECT_NAME', default=None),
        project_domain_id = env('OS_PROJECT_DOMAIN_ID', default=None),
        project_domain_name = env('OS_PROJECT_DOMAIN_NAME', default=None))
    sess = session.Session(auth=auth)
    keystone = keystoneclient.Client(session=sess)
    return keystone

def nova_client(user):
    return novaclient.Client('2.1', session=user['session'])

def glance_client(user):
    return glanceclient.Client('1', session=user['session'])

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
        auth_url = env('OS_AUTH_URL', default=None),
        password = user['password'],
        user_id = user['user'].id,
        project_id = user['user'].default_project_id)
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
    role = get_role(keystone, user['role'])
    keystone.roles.grant(role.id, user=_user.id, project=project.id)
    return _user

def delete_user(keystone, user):
    try:
        user = get_user(keystone, user['username'])
        keystone.users.delete(user)
    except ValueError as e:
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

def create_server(name, vm, users, timeout=300):
    nova = nova_client(users[vm['user']])
    glance = glance_client(users[vm['user']])
    flavor = get_flavor(nova, vm['flavor'])
    image = get_image(glance, vm['image'])
    instance = nova.servers.create(
        name=name,
        image=image,
        flavor=flavor,
    )
    _timeout = 0
    while instance.status != 'ACTIVE':
        sys.stderr.write('Waiting server ACTIVE: %s\n' % name)
        time.sleep(5)
        _timeout += 5
        if _timeout > timeout:
            raise RuntimeError("Timeout!")
        instance = nova.servers.get(instance.id)
