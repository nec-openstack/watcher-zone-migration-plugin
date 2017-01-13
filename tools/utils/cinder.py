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

from __future__ import print_function
import sys
import time

from cinderclient import client as cinderclient
from cinderclient import exceptions as cinder_exections


def cinder_client(session):
    return cinderclient.Client(2, session=session)


def get_volume(cinder, name_or_id):
    try:
        volume = cinder.volumes.get(name_or_id)
        return volume
    except cinder_exections.NotFound:
        return cinder.volumes.find(name=name_or_id)


def wait_instance(
    cinder,
    instance,
    timeout=300,
    target_states=('in-use', 'available', 'downloading'),
    transition_states=('creating'),
    status_attr='status',
    ):
    _timeout = 0
    status = getattr(instance, status_attr)
    while status not in target_states:
        if status not in transition_states:
            raise RuntimeError(
                'Fail to volume "%s": %s (%s)' % (
                    target_states,
                    instance.name,
                    status
                )
            )

        sys.stderr.write(
            'Waiting volume %s: %s (%s)\n' % (
                target_states,
                instance.name,
                status)
        )
        time.sleep(5)
        _timeout += 5
        if _timeout > timeout:
            raise RuntimeError("Timeout!")
        instance = cinder.volumes.get(instance.id)
        status = getattr(instance, status_attr)
