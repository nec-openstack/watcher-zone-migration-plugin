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
import sys

from utils import common
from utils import keystone
from utils import nova


env_file = sys.argv[1]
target_env = common.load_target_env(env_file)

admin = keystone.admin_session(**target_env['env']['admin'])
target_env['env']['admin'] = admin
keystone_client = keystone.keystone_client(admin)

users = keystone.find_or_create_users(keystone_client, target_env['user'])

nova.delete_servers(target_env, target_env['vm'], users)
keystone.delete_users(keystone_client, target_env['user'])
