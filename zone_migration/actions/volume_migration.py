import time

import six

from oslo_log import log
import voluptuous

from watcher.applier.actions import base
from watcher.common import utils

LOG = log.getLogger(__name__)


class VolumeMigrationAction(base.BaseAction):

    DST_HOSTNAME = "dst_hostname"

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
            voluptuous.Required(self.DST_HOSTNAME):
                voluptuous.Any(*six.string_types)
        })

    @property
    def volume_id(self):
        return self.input_parameters.get(self.RESOURCE_ID)

    @property
    def dst_hostname(self):
        return self.input_parameters.get(self.DST_HOSTNAME)

    def migrate(self, volume_id, dst_hostname, retry=120):
        volume = self.cinder.volumes.get(volume_id)
        if not volume:
            raise Exception("Volume not found: %s" % volume_id)
        else:
            source_hostname = getattr(volume,
                                      'os-vol-host-attr:host')
            LOG.debug(
                "Instance %s found on host '%s'." % (
                    volume_id, source_hostname))
            self.cinder.volumes.migrate_volume(
                volume, dst_hostname, False, False)
            while getattr(volume,
                          'os-vol-host-attr:host') == source_hostname \
                    and getattr(volume, 'migration_status') != 'error' \
                    and retry:
                volume = self.cinder.volumes.get(volume_id)
                LOG.debug('Waiting the migration of {0}'.format(volume))
                time.sleep(5)
                retry -= 1
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
        return self.migrate(self.volume_id, self.dst_hostname)

    def revert(self):
        LOG.debug("Do nothing to Revert action of VolumeMigration")

    def pre_condition(self):
        self.cinder = self.osc.cinder()

    def post_condition(self):
        pass
