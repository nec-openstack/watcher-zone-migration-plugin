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

import random
import string
import time

import six

from oslo_config import cfg
from oslo_log import log
import voluptuous

from cinderclient import client as local_cinder
from cinderclient import exceptions as ce
from keystoneauth1 import loading
from keystoneauth1 import session
from watcher.applier.actions import base
from watcher.common import utils
from zone_migration import conf

LOG = log.getLogger(__name__)
CONF = cfg.CONF
CONF = conf.CONF


def randomString(n):
    return ''.join([random.choice(
        string.ascii_letters + string.digits) for i in range(n)])


class VolumeUpdateAction(base.BaseAction):

    TEMP_USER_NAME = "tempuser"
    TEMP_USER_PASSWORD = "password"
    TEMP_USER_ROLE = "admin"
    DST_TYPE = "dst_type"

    def __init__(self, config, osc=None):
        super(VolumeUpdateAction, self).__init__(config)
        self._temp_user_name = self.TEMP_USER_NAME + randomString(10)
        self._temp_user_password = self.TEMP_USER_PASSWORD + randomString(10)

    def check_uuid(self, value):
        if (value is not None and
                len(value) > 0 and not
                utils.is_uuid_like(value)):
            raise voluptuous.Invalid(_("The parameter "
                                       "is invalid."))

    @property
    def schema(self):
        return voluptuous.Schema({
            voluptuous.Required(self.RESOURCE_ID):
                self.check_uuid,
            voluptuous.Required(self.DST_TYPE):
                voluptuous.Any(*six.string_types)
        })

    @property
    def server_id(self):
        return self.src_volume_attr['attachments'][0]['server_id']

    @property
    def attachment_id(self):
        return self.input_parameters.get(self.RESOURCE_ID)

    @property
    def dst_type(self):
        return self.input_parameters.get(self.DST_TYPE)

    def migrate(self, server_id, attachment_id, dst_type):
        retry = CONF.zone_migration.retry
        retry_interval = CONF.zone_migration.retry_interval
        user = self.keystone.users.find(name=self.temp_user_name)

        LOG.debug("auth_url: " + CONF.watcher_clients_auth.auth_url)
        LOG.debug("user_id: " + user.id)
        LOG.debug("project_id: " + user.default_project_id)

        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(
            auth_url=CONF.watcher_clients_auth.auth_url,
            user_id=user.id,
            password=self.temp_user_password,
            project_id=user.default_project_id)
        sess = session.Session(auth=auth)
        cinder = local_cinder.Client(2, session=sess)
        # create new volume
        new_volume = cinder.volumes.create(
            self.src_volume_attr["size"],
            name=self.src_volume_attr["name"],
            volume_type=dst_type,
            availability_zone=self.src_volume_attr["availability_zone"])
        while getattr(new_volume, 'status') != 'available':
            new_volume = cinder.volumes.get(new_volume.id)
            LOG.debug('Waiting volume creation of {0}'.format(new_volume))
            time.sleep(retry_interval)
        LOG.debug("Volume %s was created successfully." % new_volume)
        # do volume update
        LOG.debug(
            "Volume %s is now on host %s." % (
                self.attachment_id, self.src_volume_attr["host"]))
        self.nova.volumes.update_server_volume(
            self.server_id, self.attachment_id, new_volume.id)
        while getattr(new_volume, 'status') != 'in-use' and retry:
            new_volume = self.cinder.volumes.get(new_volume.id)
            LOG.debug('Waiting volume update to {0}'.format(new_volume))
            time.sleep(retry_interval)
            retry -= 1
            LOG.debug("retry count: %s" % retry)
        if getattr(new_volume, 'status') != "in-use":
            raise Exception("Volume update retry timeout or error : "
                            "volume %s is now on host '%s'." % (
                                self.attachment_id,
                                self.src_volume_attr["host"]))

        host_name = getattr(new_volume, "os-vol-host-attr:host")
        LOG.debug(
            "Volume update succeeded : "
            "Volume %s is now on host '%s'." % (
                new_volume.id, host_name))
        # delete old volume
        cinder.volumes.delete(self.attachment_id)
        while True:
            try:
                self.cinder.volumes.get(self.attachment_id)
                LOG.debug('Waiting volume deletion of {0}'.format(
                    self.attachment_id))
                time.sleep(retry_interval)
            except ce.NotFound:
                break
        LOG.debug("Volume %s was deleted successfully." % self.attachment_id)

    def get_volume_attr(self, volume_id):
        volume = self.cinder.volumes.get(volume_id)
        if not volume:
            raise Exception("Volume not found: %s" % volume_id)
        size = getattr(volume, 'size')
        name = getattr(volume, 'name')
        tenant_id = getattr(volume, 'os-vol-tenant-attr:tenant_id')
        availability_zone = getattr(volume, 'availability_zone')
        attachments = getattr(volume, 'attachments')
        host = getattr(volume, 'os-vol-host-attr:host')
        volume_type = getattr(volume, 'volume_type')
        return {
            "attachments": attachments,
            "size": size,
            "name": name,
            "tenant_id": tenant_id,
            "availability_zone": availability_zone,
            "host": host,
            "volume_type": volume_type
        }

    @property
    def temp_user_name(self):
        return self._temp_user_name

    @property
    def temp_user_password(self):
        return self._temp_user_password

    def create_temp_user(self):
        project = self.keystone.projects.get(self.src_volume_attr["tenant_id"])
        domain = self.keystone.domains.find(
            name=CONF.watcher_clients_auth.user_domain_name)
        self.keystone.users.create(self.temp_user_name,
                                   password=self.temp_user_password,
                                   domain=domain,
                                   project=project)
        LOG.debug("created user: " + self.temp_user_name)
        role = self.keystone.roles.find(name=self.TEMP_USER_ROLE)
        user = self.keystone.users.find(name=self.temp_user_name)
        self.keystone.roles.grant(role.id, user=user.id, project=project.id)

    def execute(self):
        return self.migrate(self.server_id, self.attachment_id, self.dst_type)

    def revert(self):
        LOG.debug("Do nothing to Revert action of VolumeUpdate")

    def pre_condition(self):
        self.nova = self.osc.nova()
        self.cinder = self.osc.cinder()
        self.keystone = self.osc.keystone()
        self.src_volume_attr = self.get_volume_attr(self.attachment_id)
        self.create_temp_user()

    def post_condition(self):
        user = self.keystone.users.find(name=self.temp_user_name)
        if user:
            self.keystone.users.delete(user)
