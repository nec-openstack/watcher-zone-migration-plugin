設定
====

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
     - my_message: 0, nop: 0, sleep: 0, live_migration: 0, cold_migration: 0,volume_migration: 0, volume_update: 0, volume_retype: 0
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
