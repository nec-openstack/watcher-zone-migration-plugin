from watcher._i18n import _
from watcher.decision_engine.goal import base
from watcher.decision_engine.goal.efficacy import specs


class ZoneMigration(base.Goal):

    @classmethod
    def get_name(cls):
        return "zone_migration"

    @classmethod
    def get_display_name(cls):
        return _("Zone Migration")

    @classmethod
    def get_translatable_display_name(cls):
        return "Zone Migration"

    @classmethod
    def get_efficacy_specification(cls):
        return specs.Unclassified()
