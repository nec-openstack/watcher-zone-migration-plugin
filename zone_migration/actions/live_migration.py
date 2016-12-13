import time

import six

from oslo_log import log
import voluptuous

from watcher._i18n import _LC
from watcher.applier.actions import base
from watcher.common import utils

LOG = log.getLogger(__name__)


class LiveMigrationAction(base.BaseAction):

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
            voluptuous.Required(self.RESOURCE_ID): self.check_resource_id,
            self.DST_HOSTNAME: voluptuous.Any(None, *six.string_types)
        })

    @property
    def instance_id(self):
        return self.input_parameters.get(self.RESOURCE_ID)

    @property
    def dst_hostname(self):
        return self.input_parameters.get(self.DST_HOSTNAME)

    def migrate(self, instance_id, dst_hostname, retry=120):
        try:
            instance = self.nova.servers.get(instance_id)
            if not instance:
                LOG.error("Instance not found: %s" % instance_id)
                return False
            else:
                source_hostname = getattr(instance, 'OS-EXT-SRV-ATTR:host')
                LOG.debug(
                    "Instance %s found on host '%s'." % (instance_id, source_hostname))
                if not dst_hostname:
                    instance.live_migrate()
                else:
                    instance.live_migrate(host=dst_hostname)
                while getattr(instance,
                              'OS-EXT-SRV-ATTR:host') == source_hostname \
                        and retry:
                    instance = self.nova.servers.get(instance.id)
                    LOG.debug(
                        'Waiting the migration of {0}'.format(instance))
                    time.sleep(1)
                    retry -= 1
                host_name = getattr(instance, 'OS-EXT-SRV-ATTR:host')
                if source_hostname == host_name:
                    return False
                LOG.debug(
                    "Live migration succeeded : "
                    "instance %s is now on host '%s'." % (instance_id, host_name))
                return True
        except Exception as exc:
            LOG.exception(exc)
            LOG.critical(_LC("Unexpected error occurred. Migration failed for "
                             "instance %s. Leaving instance on previous "
                             "host."), self.instance_id)
            return False

    def execute(self):
        return self.migrate(self.instance_id, self.dst_hostname)

    def revert(self):
        LOG.debug("Do nothing to Revert action of LiveMigration")
        return True

    def pre_condition(self):
        self.nova = self.osc.nova()

    def post_condition(self):
        pass
