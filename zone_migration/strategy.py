import abc

import six

from watcher._i18n import _
from watcher.decision_engine.strategy.strategies import base

@six.add_metaclass(abc.ABCMeta)
class ZoneMigrationStrategy(base.BaseStrategy):

    def __init__(self, config, osc=None):
        super(ZoneMigrationStrategy, self).__init__(config, osc)

    def pre_execute(self):
        pass

    def do_execute(self):
        pass

    def post_execute(self):
        pass

    @classmethod
    def get_goal_name(cls):
        return "zone_migration"

    @classmethod
    def get_name(cls):
        return "zone_migration"

    @classmethod
    def get_display_name(cls):
        return _("Zone migration strategy")

    @classmethod
    def get_translatable_display_name(cls):
        return "Zone migration strategy"

    


