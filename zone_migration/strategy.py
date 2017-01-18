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

import abc

import six

from oslo_log import log

from watcher._i18n import _
from watcher.decision_engine.strategy.strategies import base

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class ParallelMigrationStrategy(base.BaseStrategy):

    VM = "vm"
    VOLUME = "volume"
    ACTIVE = "active"
    SHUTOFF = "shutoff"
    AVAILABLE = "available"
    IN_USE = "in-use"
    LIVE_MIGRATION = "live_migration"
    COLD_MIGRATION = "cold_migration"
    VOLUME_MIGRATION = "volume_migration"
    VOLUME_RETYPE = "volume_retype"
    VOLUME_UPDATE = "volume_update"
    STATUS = "status"
    DST_HOSTNAME = "dst_hostname"
    DST_TYPE = "dst_type"

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
                dst_type = dict.get(self.DST_TYPE)
                if key == self.VM:
                    if resource_status == self.ACTIVE:
                        # do live migration
                        self._live_migration(resource_id, dst_hostname)
                    elif resource_status == self.SHUTOFF:
                        # do cold migration
                        # cold migration can not specify dest_hostname
                        self._cold_migration(resource_id)
                    else:
                        raise Exception("Wrong status: %s." % resource_status)
                elif key == self.VOLUME:
                    if resource_status == self.IN_USE:
                        # do novavolume update
                        self._volume_update(resource_id, dst_type)
                    elif resource_status == self.AVAILABLE:
                        # detached volume with no snapshots
                        # do cinder migrate
                        self._volume_retype(resource_id, dst_type)
                    else:
                        raise Exception("Wrong status: %s." % resource_status)
                else:
                    raise Exception("Wrong key: %s." % key)

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

    def _volume_update(self, resource_id, dst_type):
        parameters = {self.DST_TYPE: dst_type}
        self.solution.add_action(
            action_type=self.VOLUME_UPDATE,
            resource_id=resource_id,
            input_parameters=parameters)

    def _volume_migrate(self, resource_id, dst_hostname):
        parameters = {self.DST_HOSTNAME: dst_hostname}
        self.solution.add_action(
            action_type=self.VOLUME_MIGRATION,
            resource_id=resource_id,
            input_parameters=parameters)

    def _volume_retype(self, resource_id, dst_type):
        parameters = {self.DST_TYPE: dst_type}
        self.solution.add_action(
            action_type=self.VOLUME_RETYPE,
            resource_id=resource_id,
            input_parameters=parameters)

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
                                 "dst_hostname": "vm_dest_hostname1"},
                             "instance_id2":
                                {"status": "shutoff"}},
                         "volume":
                            {"cinder_id1":
                                {"status": "available",
                                 "dst_type": "volume_dst_type"},
                             "cinder_id2":
                                {"status": "in-use",
                                 "dst_type": "volume_dst_type"}}}
                    }
                }
            }
