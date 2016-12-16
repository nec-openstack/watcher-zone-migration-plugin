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

from oslo_config import cfg
from oslo_log import log
import voluptuous

from watcher.applier.actions import base
from watcher.common import utils

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class VolumeUpdateAction(base.BaseAction):

    ATTACHMENT_ID = "attachment_id"

    TEMP_USER_NAME = "tempuser"
    TEMP_USER_PASSWORD = "password"
    TEMP_USER_ROLE = "Member"

    def check_uuid(self, value):
        if (value is not None and
                len(value) > 0 and not
                utils.is_uuid_like(value)):
            raise voluptuous.Invalid(_("The parameter "
                                       "is invalid."))

    @property
    def schema(self):
        return voluptuous.Schema({
            voluptuous.Required(self.RESOURCE_ID): self.check_uuid,
            voluptuous.Required(self.ATTACHMENT_ID): self.check_uuid
        })

    @property
    def server_id(self):
        return self.input_parameters.get(self.RESOURCE_ID)

    @property
    def attachment_id(self):
        return self.input_parameters.get(self.ATTACHMENT_ID)

    def migrate(self, server_id, attachment_id, retry=120):
        from keystoneauth1 import loading
        from keystoneauth1 import session
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(
            auth_url=CONF.keystone_authtoken.auth_uri,
            username=self.temp_user_name,
            password=self.TEMP_USER_PASSWORD,
            project_id=self.src_volume_attr["tenant_id"])
        sess = session.Session(auth=auth)
        from cinderclient import client as cinder
        cinder = cinder.Client(2, session=sess)
        new_volume = cinder.volumes.create(
            self.src_volume_attr["size"],
            name=self.src_volume_attr["name"],
            availability_zone=self.src_volume_attr["availability_zone"])
        # TODO(hidekazu): wait until new_volume available
        time.sleep(60)
        # do volume update
        LOG.debug(
            "Volume %s is now on host %s." % (
                self.attachment_id, self.src_volume_attr["host"]))
        self.nova.volumes.update_server_volume(
            self.server_id, self.attachment_id, new_volume.id)
        while getattr(new_volume, 'status') != 'in-use' and retry:
            new_volume = self.cinder.volumes.get(new_volume.id)
            LOG.debug('Waiting volume update of {0}'.format(new_volume))
            time.sleep(5)
            retry -= 1
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

    def get_volume_attr(self, volume_id):
        volume = self.cinder.volumes.get(volume_id)
        if not volume:
            raise Exception("Volume not found: %s" % volume_id)
        size = getattr(volume, 'size')
        name = getattr(volume, 'name')
        tenant_id = getattr(volume, 'os-vol-tenant-attr:tenant_id')
        availability_zone = getattr(volume, 'availability_zone')
        host = getattr(volume, 'os-vol-host-attr:host')
        return {
            "size": size,
            "name": name,
            "tenant_id": tenant_id,
            "availability_zone": availability_zone,
            "host": host
        }

    @property
    def temp_user_name(self):
        return self.TEMP_USER_NAME + self.randomString(10)

    def create_temp_user(self):
        project_id = self.src_volume_attr["tenant_id"]
        self.keystone.users.create(self.temp_user_name,
                                   password=self.TEMP_USER_PASSWORD,
                                   project=self.src_volume_attr["tenant_id"])
        role = self.keystone.roles.find(name=self.TEMP_USER_ROLE)
        user = self.keystone.users.find(name=self.temp_user_name)
        self.keystone.roles.grant(role.id, user=user.id, project=project_id)

    def randomString(n):
        return ''.join([random.choice(
            string.ascii_letters + string.digits) for i in range(n)])

    def execute(self):
        return self.migrate(self.server_id, self.attachment_id)

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
        self.keystone.users.delete(user)
