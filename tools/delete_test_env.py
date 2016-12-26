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

env_file = sys.argv[1]
target_env = common.load_target_env(env_file)

admin = common.admin_session(**target_env['env']['admin'])
target_env['env']['admin'] = admin
keystone = common.keystone_client(admin)

common.delete_users(keystone, target_env['user'])
