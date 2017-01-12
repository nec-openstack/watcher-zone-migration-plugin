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

from keystoneauth1.exceptions import http as ks_exceptions
from keystoneauth1 import loading
from keystoneauth1 import session
from keystoneclient.v3 import client as keystoneclient


def admin_session(**kwargs):
    loader = loading.get_plugin_loader('v3password')
    auth = loader.load_from_options(**kwargs)
    return session.Session(auth=auth)


def keystone_client(session):
    keystone = keystoneclient.Client(session=session)
    return keystone


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


def create_session(auth_url, user):
    loader = loading.get_plugin_loader('v3password')
    auth = loader.load_from_options(
        auth_url=auth_url,
        password=user['password'],
        user_id=user['user'].id,
        project_id=user['user'].default_project_id)
    return session.Session(auth=auth)


def create_user(keystone, name, user):
    project = get_project(keystone, user['project'])
    domain = get_domain(keystone, user['domain'])
    _user = keystone.users.create(
        name,
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
        user = get_user(keystone, user)
        keystone.users.delete(user)
    except ValueError:
        pass
