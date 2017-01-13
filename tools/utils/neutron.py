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

from neutronclient.common import exceptions as neutron_exceptions
from neutronclient.v2_0 import client as neutronclient


def neutron_client(session):
    return neutronclient.Client(session=session)


def get_network(neutron_client, name_or_id):
    try:
        return neutron_client.show_network(name_or_id)['network']
    except neutron_exceptions.NotFound:
        networks = neutron_client.list_networks(name=name_or_id)
        if len(networks) == 0:
            raise ValueError('Network not Found: %s' % name_or_id)
        if len(networks) > 1:
            raise ValueError('Network name seems ambiguous: %s' % name_or_id)
        return networks['networks'][0]
