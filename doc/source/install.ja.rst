================================
zone-migration インストール手順
================================

前提条件
========

* CentOS Linux release 7.3.1611 (Core)
* Watcher 0.33.0
* zone-migration master
* 未アタッチボリュームのマイグレーションは異なるタイプに行う


インストール
============

zone-migrationインストール
--------------------------

.. code-block:: sh

    $ workon watcher
    $ pip install git+https://github.com/nec-openstack/watcher-zone-migration-plugin.git

タグまたはブランチを指定するなら

.. code-block:: sh

    $ pip install git+https://github.com/nec-openstack/watcher-zone-migration-plugin.git@ {{ tag or branch }

とする。たとえばタグ 0.1.2 を指定するなら

.. code-block:: sh

    $ pip install git+https://github.com/nec-openstack/watcher-zone-migration-plugin.git@0.1.2 


設定ファイル（/etc/watcher/watcher.conf）変更
---------------------------------------------

以下を追加します。

.. code-block:: sh

    [watcher_planners.default]
    # do not add quote or double quote
    weights = my_message: 0, nop: 0, sleep: 0, live_migration: 0, cold_migration: 0, volume_migration: 0, volume_update: 0, volume_retype: 0

    [watcher_applier]
    workflow_engine = parallel

    [zone_migration]
    # Number of retries migrate state changes to see, default value is 120
    retry = 120
    # seconds of retry interval migrate state changes to see, default value is 5
    retry_interval = 5

サービス再起動
---------------

.. code-block:: sh

    $ ps -ef |grep watcher
    hid-nak+  4749  6385  0 20:46 pts/0    00:00:00 grep --color=auto watcher
    hid-nak+ 18188  6385  2 18:05 pts/0    00:03:47 /home/hid-nakamura/.virtualenvs/watcher/bin/python /home/hid-nakamura/.virtualenvs/watcher/bin/watcher-decision-engine
    hid-nak+ 18235  6385  1 18:05 pts/0    00:02:59 /home/hid-nakamura/.virtualenvs/watcher/bin/python   /home/hid-nakamura/.virtualenvs/watcher/bin/watcher-applier
    hid-nak+ 18918  6385  1 18:10 pts/0    00:02:14 /home/hid-nakamura/.virtualenvs/watcher/bin/python /home/hid-nakamura/.virtualenvs/watcher/bin/watcher-api
    hid-nak+ 18927 18918  0 18:10 pts/0    00:00:00 /home/hid-nakamura/.virtualenvs/watcher/bin/python /home/hid-nakamura/.virtualenvs/watcher/bin/watcher-api
    hid-nak+ 18928 18918  0 18:10 pts/0    00:00:00 /home/hid-nakamura/.virtualenvs/watcher/bin/python /home/hid-nakamura/.virtualenvs/watcher/bin/watcher-api
    $ sudo kill 18188
    $ sudo kill 18235
    $ sudo kill 18918

    $ watcher-api &
    $ watcher-decision-engine &
    $ watcher-applier &

動作確認
========

Goal と Strategy にzone_migrationが表示されることを確認する。

.. code-block:: sh

    $ watcher goal list
    /home/hid-nakamura/.virtualenvs/watcher/lib/python2.7/site-packages/keystoneauth1/adapter.py:135: UserWarning: Using keystoneclient sessions has been deprecated. Please update your software to use keystoneauth1.
    warnings.warn('Using keystoneclient sessions has been deprecated. '
    +--------------------------------------+----------------------+----------------------+
    | UUID                                 | Name                 | Display name         |
    +--------------------------------------+----------------------+----------------------+
    | 0c2dc90a-835a-4b84-afca-5dffff9ad246 | dummy                | Dummy goal           |
    | 666bd7ba-93c5-4038-8179-1860b2dc4786 | workload_balancing   | Workload Balancing   |
    | 27580fd7-67e9-43e6-a38d-3359f27484de | server_consolidation | Server Consolidation |
    | 88a3df95-b14d-4208-b462-370893a4aa13 | thermal_optimization | Thermal Optimization |
    | 37986b34-6d11-489d-bacc-03839457ee76 | airflow_optimization | Airflow Optimization |
    | 62e59a66-1b92-4d7b-8deb-d8c65817a225 | unclassified         | Unclassified         |
    | 192afd7b-84b2-48a0-b755-b2b1b5a3227b | zone_migration       | Zone Migration       |
    +--------------------------------------+----------------------+----------------------+
    $ watcher strategy list
    +------------------------------+---------------------------+------------------------------+----------------------+
    | UUID                         | Name                      | Display name                 | Goal                 |
    +------------------------------+---------------------------+------------------------------+----------------------+
    | 1889e3e3-7c64-4a39-bfd3-fefb | dummy                     | Dummy strategy               | dummy                |
    | 262efb15                     |                           |                              |                      |
    | 1c62ae78-7199-4aa5-a1d6-5da9 | dummy_with_scorer         | Dummy Strategy using sample  | dummy                |
    | cb6357bd                     |                           | Scoring Engines              |                      |
    | 76be3d46-ab37-4001-9637-7dfc | outlet_temperature        | Outlet temperature based     | thermal_optimization |
    | fa04d80c                     |                           | strategy                     |                      |
    | ed3e181f-eb6a-43a2-a97b-     | vm_workload_consolidation | VM Workload Consolidation    | server_consolidation |
    | f56f9e7a1e7b                 |                           | Strategy                     |                      |
    | 79d99fcc-4569-44d0-b0e8-6084 | basic                     | Basic offline consolidation  | server_consolidation |
    | 5e24fc12                     |                           |                              |                      |
    | 38e7720b-475b-               | workload_stabilization    | Workload stabilization       | workload_balancing   |
    | 43a7-8192-5b5403ef879f       |                           |                              |                      |
    | 5972ed8c-b028-4e8a-8b5b-     | workload_balance          | Workload Balance Migration   | workload_balancing   |
    | 6f009ff59a55                 |                           | Strategy                     |                      |
    | 34e8b7c9-5c10-44ab-9408-fd9c | uniform_airflow           | Uniform airflow migration    | airflow_optimization |
    | 062dca31                     |                           | strategy                     |                      |
    | 85d39b54-6bd4-4cd4-8e92-9204 | parallel_migration        | Parallel migration strategy  | zone_migration       |
    | 98388742                     |                           |                              |                      |
    +------------------------------+---------------------------+------------------------------+----------------------+

再インストール
==============

インストール後、サービス再起動してください。
