import sys

from utils import common

env_file = sys.argv[1]
target_env = common.load_target_env(env_file)

keystone = common.keystone_admin_client()

users = common.create_users(keystone, target_env['user'])
