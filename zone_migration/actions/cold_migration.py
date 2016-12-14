import time

from oslo_log import log
import voluptuous

from watcher._i18n import _LC
from watcher.applier.actions import base
from watcher.common import utils

LOG = log.getLogger(__name__)


class ColdMigrationAction(base.BaseAction):

    VERIFY_RESIZE = 'VERIFY_RESIZE'

    def check_resource_id(self, value):
        if (value is not None and
                len(value) > 0 and not
                utils.is_uuid_like(value)):
            raise voluptuous.Invalid(_("The parameter "
                                       "resource_id is invalid."))

    @property
    def schema(self):
        return voluptuous.Schema({
            voluptuous.Required(self.RESOURCE_ID): self.check_resource_id
        })

    @property
    def instance_id(self):
        return self.input_parameters.get(self.RESOURCE_ID)

    def migrate(self, instance_id, retry=120):
        instance = self.nova.servers.get(instance_id)
        if not instance:
            raise Exception("Instance not found: %s" % instance_id)
        else:
            source_hostname = getattr(instance, 'OS-EXT-SRV-ATTR:host')
            LOG.debug(
                "Instance %s found on host '%s'." % (
                    instance_id, source_hostname))
            instance.migrate()
            while getattr(instance,
                          'status') != self.VERIFY_RESIZE \
                    and retry:
                instance = self.nova.servers.get(instance.id)
                LOG.debug(
                    'Waiting the migration of {0}'.format(instance))
                time.sleep(5)
                retry -= 1
            host_name = getattr(instance, 'OS-EXT-SRV-ATTR:host')
            if source_hostname == host_name:
                raise Exception("Migration retry timeout: "
                                "instance %s is now on host '%s'." % (
                                    instance_id, host_name))
            LOG.debug(
                "Migration succeeded : "
                "instance %s is now on host '%s'." % (instance_id, host_name))
            LOG.debug('Start confirm resize')
            instance.confirm_resize()
            LOG.debug('End confirm resize')

    def execute(self):
        return self.migrate(self.instance_id)

    def revert(self):
        LOG.debug("Do nothing to Revert action of Migration")

    def pre_condition(self):
        self.nova = self.osc.nova()

    def post_condition(self):
        pass
