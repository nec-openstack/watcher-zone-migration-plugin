import abc

import six

from oslo_log import log

from watcher._i18n import _
from watcher.decision_engine.strategy.strategies import base

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class ParallelMigrationStrategy(base.BaseStrategy):

    VM = "vm"
    STORAGE = "storage"
    ACTIVE = "active"
    SHUTOFF = "shutoff"
    LIVE_MIGRATION = "live_migration"
    COLD_MIGRATION = "cold_migration"
    STATUS = "status"
    DST_HOSTNAME = "dst_hostname"

    def __init__(self, config, osc=None):
        super(ParallelMigrationStrategy, self).__init__(config, osc)

    def pre_execute(self):
        pass

    def do_execute(self):
        params = self.input_parameters.params
        for key, value in params.iteritems():
            for resource_id, dict in value.items():
                resource_status = dict.get(self.STATUS)
                dst_hostname = dict.get(self.DST_HOSTNAME)
                if key == self.VM:
                    if resource_status == self.ACTIVE:
                        # do live migration
                        self._live_migration(resource_id, dst_hostname)
                    elif resource_status == self.SHUTOFF:
                        # do cold migration
                        # cold migration can not specify dest_hostname
                        self._cold_migration(resource_id)
                elif key == self.STORAGE:
                    if resource_status == self.ACTIVE:
                        # do novavolume update
                        self._volume_update(resource_id)
                    else:
                        # do cinder migrate
                        self._cinder_migrate(resource_id)

    def _live_migration(self, resource_id, dst_hostname):
        parameters = {self.DST_HOSTNAME: dst_hostname}
        self.solution.add_action(
            action_type=self.LIVE_MIGRATION,
            resource_id=resource_id,
            input_parameters=parameters)

    def _cold_migration(self, resource_id):
        self.solution.add_action(
            action_type=self.COLD_MIGRATION,
            resource_id=resource_id,
            input_parameters={})

    def _volume_update(self, resource_id):
        pass

    def _cinder_migrate(self, resource_id):
        pass

    def post_execute(self):
        pass

    @classmethod
    def get_goal_name(cls):
        return "zone_migration"

    @classmethod
    def get_name(cls):
        return "parallel_migration"

    @classmethod
    def get_display_name(cls):
        return _("Parallel migration strategy")

    @classmethod
    def get_translatable_display_name(cls):
        return "Parallel migration strategy"

    @classmethod
    def get_schema(cls):
        return {
            "properties": {
                "params": {
                    "description": "",
                    "type": "object",
                    "default":
                        {"vm":
                            {"instance_id1":
                                {"status": "active",
                                 "dest_hostname": "vm_dest_hostname1"},
                             "instance_id2":
                                {"status": "stop"}},
                         "storage":
                            {"cinder_id1":
                                {"status": "active",
                                 "dest_hostname": "strorage_dest_hostname1"},
                             "cinder_id2":
                                {"status": "stop"}}}
                    }
                }
            }
