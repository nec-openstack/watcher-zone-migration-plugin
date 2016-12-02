import abc

import six

from oslo_log import log

from watcher._i18n import _
from watcher.decision_engine.strategy.strategies import base

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class ParallelMigrationStrategy(base.BaseStrategy):

    NOP = "nop"

    def __init__(self, config, osc=None):
        super(ParallelMigrationStrategy, self).__init__(config, osc)

    def pre_execute(self):
        pass

    def do_execute(self):
        para1 = self.input_parameters.para1
        para2 = self.input_parameters.para2
        LOG.debug("para1:" + para1)
        LOG.debug("para2:" + para2)

        self.solution.add_action(action_type=self.NOP,
                                 input_parameters={'message': para1})
        self.solution.add_action(action_type=self.NOP,
                                 input_parameters={'message': para2})

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
                "para1": {
                    "description": "string parameter one",
                    "type": "string",
                    "default": "hello zone one"
                },
                "para2": {
                    "description": "string parameter two",
                    "type": "string",
                    "default": "hello zone two"
                }
            }
        }
