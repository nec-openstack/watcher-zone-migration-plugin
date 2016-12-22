import sys

from utils import common

env_file = sys.argv[1]
target_env = common.load_target_env(env_file)

admin = common.admin_session(**target_env['env']['admin'])
target_env['env']['admin'] = admin
keystone = common.keystone_client(admin)

common.delete_users(keystone, target_env['user'])
users = common.create_users(keystone, target_env['user'])

common.create_server(target_env['env'], 'instance1', target_env['vm']['instance1'], users)
common.create_server(target_env['env'], 'instance2', target_env['vm']['instance2'], users)
