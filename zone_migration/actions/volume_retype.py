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

import time

import six

from oslo_log import log
import voluptuous

from watcher.applier.actions import base
from watcher.common import utils
from zone_migration import conf

LOG = log.getLogger(__name__)

CONF = conf.CONF


class VolumeRetypeAction(base.BaseAction):

    DST_TYPE = "dst_type"
    POLICY = "on-demand"

    def check_resource_id(self, value):
        if (value is not None and
                len(value) > 0 and not
                utils.is_uuid_like(value)):
            raise voluptuous.Invalid(_("The parameter "
                                       "resource_id is invalid."))

    @property
    def schema(self):
        return voluptuous.Schema({
            voluptuous.Required(self.RESOURCE_ID):
                self.check_resource_id,
            voluptuous.Required(self.DST_TYPE):
                voluptuous.Any(*six.string_types)
        })

    @property
    def volume_id(self):
        return self.input_parameters.get(self.RESOURCE_ID)

    @property
    def dst_type(self):
        return self.input_parameters.get(self.DST_TYPE)

    def retype(self, volume_id, dst_type):
        retry = CONF.zone_migration.retry
        retry_interval = CONF.zone_migration.retry_interval
        volume = self.cinder.volumes.get(volume_id)
        if not volume:
            raise Exception("Volume not found: %s" % volume_id)
        else:
            source_hostname = getattr(volume,
                                      'os-vol-host-attr:host')
            LOG.debug(
                "Instance %s found on host '%s'." % (
                    volume_id, source_hostname))
            self.cinder.volumes.retype(
                volume, dst_type, self.POLICY)
            while getattr(volume,
                          'os-vol-host-attr:host') == source_hostname \
                    and getattr(volume, 'migration_status') != 'error' \
                    and retry:
                volume = self.cinder.volumes.get(volume_id)
                LOG.debug('Waiting the migration of {0}'.format(volume))
                time.sleep(retry_interval)
                retry -= 1
                LOG.debug("retry count: %s" % retry)
            host_name = getattr(volume, 'os-vol-host-attr:host')
            if source_hostname == host_name:
                raise Exception("Volume migration retry timeout or error : "
                                "instance %s is now on host '%s'." % (
                                    volume_id, host_name))
            LOG.debug(
                "Volume migration succeeded : "
                "instance %s is now on host '%s'." % (
                    volume_id, host_name))

    def execute(self):
        return self.retype(self.volume_id, self.dst_type)

    def revert(self):
        LOG.debug("Do nothing to Revert action of VolumeRetype")

    def pre_condition(self):
        self.cinder = self.osc.cinder()

    def post_condition(self):
        pass
