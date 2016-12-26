===============================
zone_migration
===============================

zone_migration

* Free software: Apache license

Install
-------

.. code::

    pip install git+https://github.com/nec-openstack/watcher-zone-migration-plugin.git

Configuration
-------------

You have to add configuration as the following to /etc/watcher/watcher.conf:

.. code::

    [watcher_planners.default]
    weights = my_message: 0, nop: 0, sleep: 0, live_migration: 0, cold_migration: 0,
    volume_migration: 0, volume_update: 0
    [watcher_applier]
    workflow_engine = parallel

You can add configuration as the following to /etc/watcher/watcher.conf:

.. code::

    [zone_migration]
    # Number of retries migrate state changes to see, default value is 120
    retry = 120
    # seconds of retry interval migrate state changes to see, default value is 5
    retry_interval = 5
