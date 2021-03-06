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

from oslo_log import log
import six
import voluptuous

from watcher.applier.actions import base


LOG = log.getLogger(__name__)


class MyMessageAction(base.BaseAction):
    """logs a message

    The action schema is::

        schema = Schema({
         'message': str,
        })

    The `message` is the actual message that will be logged.
    """

    MESSAGE = 'message'

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
