import os
import sys
import yaml

from keystoneauth1 import loading
from keystoneauth1 import session
from keystoneauth1.exceptions.http import NotFound
from keystoneclient.v3 import client as kc_v3

def env(*args, **kwargs):
    """Returns the first environment variable set.

    If all are empty, defaults to '' or keyword arg `default`.
    """
    for arg in args:
        value = os.environ.get(arg)
        if value:
            return value
    return kwargs.get('default', '')

def get_user(keystone, name_or_id):
    try:
        user = keystone.users.get(name_or_id)
        return user
    except NotFound:
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
    except NotFound:
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
    except NotFound:
        domains = keystone.domains.list(name=name_or_id)
        if len(domains) == 0:
            raise ValueError('Domain not Found: %s' % name_or_id)
        if len(domains) > 1:
            raise ValueError('Domain name seems ambiguous: %s' % name_or_id)
        return domains[0]

def create_user(keystone, user):
    project = get_project(keystone, user['project'])
    domain = get_domain(keystone, user['domain'])
    return keystone.users.create(
        user['username'],
        password=user['password'],
        domain=domain,
        project=project,
    )

def delete_user(keystone, user):
    try:
        user = get_user(keystone, user['username'])
        keystone.users.delete(user)
    except ValueError as e:
        pass

def create_users(keystone, users={}):
    for _, user in users.items():
        create_user(keystone, user)

def delete_users(keystone, users={}):
    for _, user in users.items():
        delete_user(keystone, user)

print(sys.argv[1])
env_file = sys.argv[1]
target_env = None

with open(env_file, 'r') as io:
    target_env = yaml.load(io)

print(target_env)

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
keystone = kc_v3.Client(session=sess)

delete_users(keystone, target_env['user'])


create_users(keystone, target_env['user'])
