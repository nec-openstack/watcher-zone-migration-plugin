from oslo_log import log
import six
import voluptuous

from watcher.applier.actions import base


LOG = log.getLogger(__name__)


class MyMessageAction(base.BaseAction):

    @property
    def schema(self):
        return voluptuous.Schema({
            voluptuous.Required(self.MESSAGE): voluptuous.Any(
                voluptuous.Any(*six.string_types), None)
        })

    def execute(self):
        LOG.debug("Executing action my message: %s",
                  self.input_parameters.get("message"))
        return True

    def revert(self):
        LOG.debug("Revert action MyMessage")
        return True

    def pre_condition(self):
        pass

    def post_condition(self):
        pass
