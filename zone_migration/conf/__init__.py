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

from oslo_config import cfg

CONF = cfg.CONF

zone_migration = cfg.OptGroup(name='zone_migration',
                              title='zone migration options'
                              )

ZONE_MIGRATION_OPTS = [
    cfg.IntOpt('retry',
               default='120',
               min=1,
               required=True,
               help='Number of retries migrate state changes to see,'
                    'default value is 120.'),
    cfg.IntOpt('retry_interval',
               default='5',
               min=1,
               required=True,
               help='seconds of retry interval migrate state changes to see,'
                    'default value is 5.')
]


def register_opts(conf):
    conf.register_group(zone_migration)
    conf.register_opts(ZONE_MIGRATION_OPTS, group=zone_migration)


def list_opts():
    return [('zone_migration', ZONE_MIGRATION_OPTS)]

register_opts(CONF)
