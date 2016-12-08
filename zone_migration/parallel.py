# -*- encoding: utf-8 -*-
# Copyright (c) 2016 b<>com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import futurist

from oslo_log import log
from taskflow import engines
from taskflow.patterns import graph_flow as gf
from taskflow import task

from watcher._i18n import _LE, _LW, _LC
from watcher.applier.workflow_engine import base
from watcher.common import exception
from watcher import objects

LOG = log.getLogger(__name__)


class ParallelWorkFlowEngine(base.BaseWorkFlowEngine):
    """Taskflow as a workflow engine for Watcher

    Full documentation on taskflow at
    http://docs.openstack.org/developer/taskflow/
    """

    def decider(self, history):
        return True

    def execute(self, actions):
        try:
            flow = gf.Flow("watcher_flow")
            for a in actions:
                task = TaskFlowActionContainer(a, self)
                flow.add(task)
            executor = futurist.GreenThreadPoolExecutor(max_workers=5)
            e = engines.load(flow, engine='parallel', executor=executor)
            e.run()

        except Exception as e:
            raise exception.WorkflowExecutionException(error=e)
        finally:
            executor.shutdown()


class TaskFlowActionContainer(task.Task):
    def __init__(self, db_action, engine):
        name = "action_type:{0} uuid:{1}".format(db_action.action_type,
                                                 db_action.uuid)
        super(TaskFlowActionContainer, self).__init__(name=name)
        self._db_action = db_action
        self._engine = engine
        self.loaded_action = None

    @property
    def action(self):
        if self.loaded_action is None:
            action = self.engine.action_factory.make_action(
                self._db_action,
                osc=self._engine.osc)
            self.loaded_action = action
        return self.loaded_action

    @property
    def engine(self):
        return self._engine

    def pre_execute(self):
        try:
            self.engine.notify(self._db_action, objects.action.State.ONGOING)
            LOG.debug("Pre-condition action: %s", self.name)
            self.action.pre_condition()
        except Exception as e:
            LOG.exception(e)
            self.engine.notify(self._db_action, objects.action.State.FAILED)
            raise

    def execute(self, *args, **kwargs):
        try:
            LOG.debug("Running action: %s", self.name)

            self.action.execute()
            self.engine.notify(self._db_action, objects.action.State.SUCCEEDED)
        except Exception as e:
            LOG.exception(e)
            LOG.error(_LE('The workflow engine has failed '
                          'to execute the action: %s'), self.name)

            self.engine.notify(self._db_action, objects.action.State.FAILED)
            raise

    def post_execute(self):
        try:
            LOG.debug("Post-condition action: %s", self.name)
            self.action.post_condition()
        except Exception as e:
            LOG.exception(e)
            self.engine.notify(self._db_action, objects.action.State.FAILED)
            raise

    def revert(self, *args, **kwargs):
        LOG.warning(_LW("Revert action: %s"), self.name)
        try:
            self.action.revert()
        except Exception as e:
            LOG.exception(e)
            LOG.critical(_LC("Oops! We need a disaster recover plan."))
