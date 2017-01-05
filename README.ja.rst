===============================
zone_migration
===============================

これは `third-party plugin for Watcher`_ for zone migration です。

.. _third-party plugin for Watcher: http://docs.openstack.org/developer/watcher/dev/plugin/base-setup.html


* ライセンス: Apache license

インストール
------------

.. code::

    pip install git+https://github.com/nec-openstack/watcher-zone-migration-plugin.git

設定
-----

.. list-table:: watcher.conf
   :widths: 10 10 20 20 30 10
   :header-rows: 1

   * - セクション名
     - キー
     - 値
     - デフォルト値
     - 意味
     - 変更必須か
   * - [watcher_planners.default]
     - weights
     - my_message: 0, nop: 0, sleep: 0, live_migration: 0, cold_migration: 0,volume_migration: 0, volume_update: 0
     - change_nova_service_state:2, migrate:3, nop:0, sleep:1
     - These weights are used to schedule the actions (dict value)
     - 必須
   * - [watcher_applier]
     - workflow_engine
     - parallel
     - taskflow
     - Select the engine to use to execute the workflow (string value)
     - 必須
   * - [zone_migration]
     - retry
     - -
     - 120
     - Number of retries migrate state changes to see
     - 任意
   * - [zone_migration]
     - retry_interval
     - -
     - 5
     - Seconds of retry interval migrate state changes to see
     - 任意

使い方
--------

zone_migration ゴールとparallel_migration ストラテジーを指定してauditを作成する ::

 watcher audit create -g zone_migration -s parallel_migration -p params=<json_object>

json objectは以下の形式 ::

 {
     "vm": {
         "<vm_id>": {
             "dst_hostname": "<vm_dst_hostname>", 
             "status": "<vm_status>"
         }
     }, 
     "volume": {
         "<volume_id>": {
             "dst_hostname": "<volume_dst_hostname>", 
             "status": "<volume_status>"
         }
     }
 }

:vm:  インスタンスを対象とするならば指定する。
:vm_id: インスタンスのID。複数のインスタンスを指定するならば繰り返す。
:vm_status: ライブマイグレーションするならば active、マイグレーションするならば shutoff。
:vm_dst_hostname: ライブマイグレーション先ホスト名。指定しないならば ""。
:volume: ボリュームを対象とするならば指定する。
:volume_id: ボリュームのID。複数のボリュームを指定するならば繰り返す。
:volume_status:  アタッチされたボリュームならばin-use、デタッチされたボリュームならばavailable。
:volume_dst_hostname: デタッチされたボリュームのマイグレーション先プール名。

JSONの例
----------

インスタンスID 3b39c007-81c4-4bbe-8848-babf583d1349のインスタンスはライブマイグレーション先を指定せず、インスタンスID 9827ce18-c92f-474b-b572-95281b903daf のインスタンスは w113 にライブマイグレーションする ::

 {
     "vm": {
         "3b39c007-81c4-4bbe-8848-babf583d1349": {
             "dst_hostname": "", 
             "status": "active"
         }, 
         "9827ce18-c92f-474b-b572-95281b903daf": {
             "dst_hostname": "w113", 
             "status": "active"
         }
     }
 }

ボリュームID 5c5b71ba-c7d3-477d-b0c4-ea1958fae8feのデタッチされたボリュームをプールw113@lvm#lvmにマイグレーション、ボリュームID fddc94b1-8db4-4949-9f43-1054f13de9e3のアタッチされたボリュームを別のボリュームにアップデートする ::

 {
     "volume": {
         "5c5b71ba-c7d3-477d-b0c4-ea1958fae8fe": {
             "dst_hostname": "w113@lvm#lvm", 
             "status": "available"
         }, 
         "fddc94b1-8db4-4949-9f43-1054f13de9e3": {
             "status": "in-use"
         }
     }
 }


FAQ
---

ホスト指定できるか。

* インスタンスのライブマイグレーション

 * ホスト指定ありなしどちらも可能

* インスタンスのマイグレーション

 * ホスト指定不可（novaでホスト指定できない）

* ボリュームのマイグレーション

 * ホスト指定必須

* ボリュームの更新

 * ホスト指定不可（cinderでホスト指定してvolume作成できない）
