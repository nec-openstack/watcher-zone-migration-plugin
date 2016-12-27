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

import json
import sys

from utils import cinder
from utils import common
from utils import keystone
from utils import nova

env_file = sys.argv[1]
target_env = common.load_target_env(env_file)

admin = target_env['env'].get('admin', None)
if admin is None:
    raise ValueError("Admin information is needed in `env` section")
users = target_env.get('user', None)
if users is None:
    raise ValueError("`user` seciton is needed")

admin = keystone.admin_session(**admin)
target_env['env']['admin'] = admin
keystone_client = keystone.keystone_client(admin)

users = keystone.find_or_create_users(keystone_client, users)

vms = target_env.get('vm', {})
volumes = target_env.get('volume', {})
nova.create_servers(target_env, vms, users)
cinder.create_volumes(target_env, volumes, users)

params = {
    'vm': {},
    'volume': {}
}
for _, vm in vms.items():
    if 'ignore' != vm.get('output', ''):
        params['vm'][vm['id']] = {
            "status": vm['status'],
            "src_hostname": vm.get('src_hostname', ''),
            "dst_hostname": vm.get('dst_hostname', ''),
        }

for _, volume in volumes.items():
    if 'ignore' != volume.get('output', ''):
        params['volume'][volume['id']] = {
            "status": volume['status'],
            "src_hostname": volume.get('src_hostname', ''),
            "dst_hostname": volume.get('dst_hostname', ''),
        }

print(json.dumps(params, sort_keys=True, indent=2))
